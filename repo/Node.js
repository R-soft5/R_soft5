// server.js
const express = require('express');
const mysql = require('mysql2/promise');
const multer = require('multer');
const path = require('path');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());
app.use('/uploads', express.static('uploads'));

// 数据库连接池
const pool = mysql.createPool({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// JWT中间件
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) return res.status(401).json({ error: '未授权访问' });
    
    jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
        if (err) return res.status(403).json({ error: '令牌无效' });
        req.user = user;
        next();
    });
};

// 文件上传配置
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, 'uploads/proofs/');
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ 
    storage: storage,
    limits: { fileSize: 5 * 1024 * 1024 }, // 5MB
    fileFilter: (req, file, cb) => {
        const allowedTypes = /jpeg|jpg|png|pdf/;
        const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
        const mimetype = allowedTypes.test(file.mimetype);
        
        if (mimetype && extname) {
            return cb(null, true);
        } else {
            cb(new Error('只允许上传图片和PDF文件'));
        }
    }
});

// 1. 用户登录
app.post('/api/login', async (req, res) => {
    try {
        const { phone, password, userType } = req.body;
        
        const [rows] = await pool.execute(
            'SELECT * FROM users WHERE phone = ? AND user_type = ?',
            [phone, userType]
        );
        
        if (rows.length === 0) {
            return res.status(401).json({ error: '用户不存在' });
        }
        
        const user = rows[0];
        const validPassword = await bcrypt.compare(password, user.password);
        
        if (!validPassword) {
            return res.status(401).json({ error: '密码错误' });
        }
        
        // 如果是机构用户，获取机构信息
        let orgInfo = null;
        if (userType === 'org') {
            const [orgRows] = await pool.execute(
                'SELECT * FROM organizations WHERE user_id = ?',
                [user.id]
            );
            orgInfo = orgRows[0];
        }
        
        const token = jwt.sign(
            { id: user.id, phone: user.phone, userType: user.user_type },
            process.env.JWT_SECRET,
            { expiresIn: '24h' }
        );
        
        res.json({
            token,
            user: {
                id: user.id,
                phone: user.phone,
                nickname: user.nickname,
                userType: user.user_type,
                orgInfo
            }
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: '服务器错误' });
    }
});

// 2. 获取捐赠者的所有捐赠记录
app.get('/api/donor/donations', authenticateToken, async (req, res) => {
    try {
        if (req.user.userType !== 'donor') {
            return res.status(403).json({ error: '无权限访问' });
        }
        
        const [donations] = await pool.execute(`
            SELECT dr.*, p.title as project_title, p.cover_image, o.org_name,
                   (SELECT COUNT(*) FROM fund_usage_records fur WHERE fur.donation_id = dr.id) as usage_count
            FROM donation_records dr
            LEFT JOIN projects p ON dr.project_id = p.id
            LEFT JOIN organizations o ON p.org_id = o.id
            WHERE dr.donor_id = ?
            ORDER BY dr.created_at DESC
        `, [req.user.id]);
        
        res.json(donations);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: '服务器错误' });
    }
});

// 3. 获取单笔捐赠的去向详情
app.get('/api/donation/:id/usage', authenticateToken, async (req, res) => {
    try {
        const donationId = req.params.id;
        
        // 验证捐赠记录是否属于当前用户
        const [donation] = await pool.execute(
            'SELECT * FROM donation_records WHERE id = ? AND donor_id = ?',
            [donationId, req.user.id]
        );
        
        if (donation.length === 0 && req.user.userType === 'donor') {
            return res.status(403).json({ error: '无权查看此记录' });
        }
        
        // 获取去向登记记录
        const [usageRecords] = await pool.execute(`
            SELECT fur.*, o.org_name, u.nickname as verifier_name
            FROM fund_usage_records fur
            LEFT JOIN organizations o ON fur.org_id = o.id
            LEFT JOIN users u ON fur.verified_by = u.id
            WHERE fur.donation_id = ?
            ORDER BY fur.usage_date DESC
        `, [donationId]);
        
        res.json({
            donation: donation[0],
            usageRecords
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: '服务器错误' });
    }
});

// 4. 机构：获取可登记去向的捐赠列表
app.get('/api/org/donations-for-registration', authenticateToken, async (req, res) => {
    try {
        if (req.user.userType !== 'org') {
            return res.status(403).json({ error: '仅机构用户可访问' });
        }
        
        // 获取该机构的所有项目
        const [projects] = await pool.execute(
            'SELECT id FROM projects WHERE org_id IN (SELECT id FROM organizations WHERE user_id = ?)',
            [req.user.id]
        );
        
        const projectIds = projects.map(p => p.id);
        if (projectIds.length === 0) {
            return res.json([]);
        }
        
        // 获取已支付且未完全登记去向的捐赠
        const [donations] = await pool.execute(`
            SELECT dr.*, u.nickname as donor_nickname, p.title as project_title,
                   (SELECT COALESCE(SUM(fur.usage_amount), 0) 
                    FROM fund_usage_records fur 
                    WHERE fur.donation_id = dr.id AND fur.status != 'draft') as registered_amount
            FROM donation_records dr
            LEFT JOIN users u ON dr.donor_id = u.id
            LEFT JOIN projects p ON dr.project_id = p.id
            WHERE dr.project_id IN (?)
            AND dr.status = 'paid'
            HAVING dr.amount > registered_amount OR registered_amount = 0
            ORDER BY dr.payment_time DESC
        `, [projectIds]);
        
        res.json(donations);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: '服务器错误' });
    }
});

// 5. 机构：创建捐款去向登记
app.post('/api/usage-records', authenticateToken, upload.single('proof'), async (req, res) => {
    try {
        if (req.user.userType !== 'org') {
            return res.status(403).json({ error: '仅机构用户可访问' });
        }
        
        const { donation_id, usage_description, usage_amount, usage_date } = req.body;
        
        // 验证捐赠记录
        const [donation] = await pool.execute(`
            SELECT dr.*, p.org_id
            FROM donation_records dr
            LEFT JOIN projects p ON dr.project_id = p.id
            LEFT JOIN organizations o ON p.org_id = o.id
            WHERE dr.id = ? AND o.user_id = ?
        `, [donation_id, req.user.id]);
        
        if (donation.length === 0) {
            return res.status(403).json({ error: '无权操作此捐赠记录' });
        }
        
        // 计算已登记金额
        const [registered] = await pool.execute(
            'SELECT COALESCE(SUM(usage_amount), 0) as total FROM fund_usage_records WHERE donation_id = ? AND status != "draft"',
            [donation_id]
        );
        
        const remaining = donation[0].amount - registered[0].total;
        if (parseFloat(usage_amount) > remaining) {
            return res.status(400).json({ error: '登记金额超过剩余可登记金额' });
        }
        
        // 获取机构ID
        const [org] = await pool.execute(
            'SELECT id FROM organizations WHERE user_id = ?',
            [req.user.id]
        );
        
        let proofImageUrl = null;
        if (req.file) {
            proofImageUrl = `/uploads/proofs/${req.file.filename}`;
            
            // 保存图片信息到数据库
            await pool.execute(
                'INSERT INTO images (record_type, record_id, file_url, file_name, file_size, mime_type, uploader_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                ['usage_proof', donation_id, proofImageUrl, req.file.originalname, req.file.size, req.file.mimetype, req.user.id]
            );
        }
        
        // 创建去向登记记录
        const [result] = await pool.execute(
            `INSERT INTO fund_usage_records 
             (donation_id, org_id, usage_description, usage_amount, usage_date, proof_image_url, status) 
             VALUES (?, ?, ?, ?, ?, ?, 'submitted')`,
            [donation_id, org[0].id, usage_description, usage_amount, usage_date, proofImageUrl]
        );
        
        res.json({
            success: true,
            recordId: result.insertId,
            message: '捐款去向登记成功'
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: '服务器错误' });
    }
});

// 6. 机构：获取已登记的去向记录
app.get('/api/org/usage-records', authenticateToken, async (req, res) => {
    try {
        if (req.user.userType !== 'org') {
            return res.status(403).json({ error: '仅机构用户可访问' });
        }
        
        const [org] = await pool.execute(
            'SELECT id FROM organizations WHERE user_id = ?',
            [req.user.id]
        );
        
        const [records] = await pool.execute(`
            SELECT fur.*, dr.amount as donation_amount, p.title as project_title,
                   u.nickname as donor_nickname
            FROM fund_usage_records fur
            LEFT JOIN donation_records dr ON fur.donation_id = dr.id
            LEFT JOIN projects p ON dr.project_id = p.id
            LEFT JOIN users u ON dr.donor_id = u.id
            WHERE fur.org_id = ?
            ORDER BY fur.created_at DESC
        `, [org[0].id]);
        
        res.json(records);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: '服务器错误' });
    }
});

// 7. 捐赠：提交捐赠
app.post('/api/donate', authenticateToken, async (req, res) => {
    try {
        if (req.user.userType !== 'donor') {
            return res.status(403).json({ error: '仅捐赠者可进行捐赠' });
        }
        
        const { project_id, amount, is_anonymous, message, payment_method } = req.body;
        
        // 生成订单号
        const orderNo = 'DON' + Date.now() + Math.random().toString(36).substr(2, 9);
        
        const [result] = await pool.execute(
            `INSERT INTO donation_records 
             (donor_id, project_id, order_no, amount, is_anonymous, message, payment_method, status) 
             VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')`,
            [req.user.id, project_id, orderNo, amount, is_anonymous, message, payment_method]
        );
        
        // 更新项目已筹金额
        await pool.execute(
            'UPDATE projects SET raised_amount = raised_amount + ? WHERE id = ?',
            [amount, project_id]
        );
        
        res.json({
            success: true,
            orderNo,
            donationId: result.insertId,
            message: '捐赠订单创建成功，请完成支付'
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: '服务器错误' });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`服务器运行在端口 ${PORT}`);
});