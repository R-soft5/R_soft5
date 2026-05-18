/**
 * 登录状态管理工具
 * 在所有页面中引入此文件以管理登录状态
 */

// 通用登录状态检查函数
function checkLoginStatus() {
    const token = localStorage.getItem('userToken');
    if (!token) {
        return null;
    }
    
    try {
        const userData = JSON.parse(token);
        
        // 检查token是否过期（模拟24小时有效期）
        const loginTime = new Date(userData.loginTime);
        const now = new Date();
        const hoursDiff = Math.abs(now - loginTime) / 36e5; // 小时数
        
        if (hoursDiff > 24) {
            // token过期，清除
            localStorage.removeItem('userToken');
            return null;
        }
        
        return userData;
    } catch (e) {
        localStorage.removeItem('userToken');
        return null;
    }
}

// 检查用户是否登录
function isLoggedIn() {
    return checkLoginStatus() !== null;
}

// 获取当前用户信息
function getCurrentUser() {
    return checkLoginStatus();
}

// 获取用户类型
function getUserType() {
    const user = getCurrentUser();
    return user ? user.userType : null;
}

// 退出登录
function logout() {
    localStorage.removeItem('userToken');
    window.location.href = 'index.html';
}

// 页面加载时自动检查登录状态
document.addEventListener('DOMContentLoaded', function() {
    const user = getCurrentUser();
    
    // 如果有用户信息，更新页面显示
    if (user) {
        // 查找并更新导航栏
        const userNameElement = document.getElementById('userName');
        const logoutBtn = document.getElementById('logoutBtn');
        const loginBtns = document.querySelectorAll('.login-section');
        
        if (userNameElement) {
            let displayName = '';
            if (user.userType === 'donor') {
                displayName = `捐赠者：${user.phone || user.userId}`;
            } else if (user.userType === 'org') {
                displayName = `机构：${user.orgName || user.phone || user.orgId}`;
            }
            userNameElement.textContent = displayName;
        }
        
        if (logoutBtn) logoutBtn.style.display = 'block';
        if (loginBtns) loginBtns.forEach(btn => btn.style.display = 'none');
    }
});

// 验证码倒计时功能
function startCountdown(button, seconds = 60) {
    const originalText = button.textContent;
    button.disabled = true;
    let count = seconds;
    
    const timer = setInterval(() => {
        count--;
        button.textContent = `${count}秒后重新获取`;
        
        if (count <= 0) {
            clearInterval(timer);
            button.disabled = false;
            button.textContent = originalText;
        }
    }, 1000);
}