/* =========================================================
   AUTH JS (Complete Full Module)
   Login + Register + Social Login + Password Reset + 2FA
   ========================================================= */

/* =========================================================
   1. LOGIN
   ========================================================= */
const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async function(e) {
        e.preventDefault();

        const email = document.getElementById("email")?.value.trim();
        const password = document.getElementById("password")?.value;

        if (!email || !password) {
            showToast("Email and password are required", true);
            return;
        }

        try {
            const data = await api("/auth/login", {
                method: "POST",
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            localStorage.setItem("access_token", data.access_token);

            if (data.refresh_token) {
                localStorage.setItem("refresh_token", data.refresh_token);
            }

            // Fresh Profile fetch karke clean user state save karna
            try {
                const userProfile = await api("/auth/me");
                localStorage.setItem("user", JSON.stringify(userProfile));
            } catch (err) {
                console.warn("User profile fetch error:", err);
            }

            showToast("Login successful! Redirecting...");

            setTimeout(() => {
                window.location.href = "/dashboard";
            }, 800);

        } catch (error) {
            showToast(error.message || "Invalid credentials", true);
        }
    });
}

/* =========================================================
   2. REGISTER
   ========================================================= */
const registerForm = document.getElementById("registerForm");

if (registerForm) {
    registerForm.addEventListener("submit", async function(e) {
        e.preventDefault();

        const name = document.getElementById("name")?.value.trim();
        const email = document.getElementById("email")?.value.trim();
        const password = document.getElementById("password")?.value;

        if (!name || !email || !password) {
            showToast("All fields are required", true);
            return;
        }

        try {
            await api("/auth/register", {
                method: "POST",
                body: JSON.stringify({
                    name: name,
                    email: email,
                    password: password
                })
            });

            showToast("Registration successful! Redirecting to login...");

            setTimeout(() => {
                window.location.href = "/login";
            }, 1200);

        } catch (error) {
            showToast(error.message || "Registration failed", true);
        }
    });
}

/* =========================================================
   3. SOCIAL LOGIN REDIRECT
   ========================================================= */
function socialLogin(provider) {
    const orgId = localStorage.getItem("organization_id");
    let targetUrl = `/api/v1/auth/${provider}/login`;
    
    if (orgId && provider === 'google') {
        targetUrl += `?organization_id=${orgId}`;
    }
    
    window.location.href = targetUrl;
}

/* =========================================================
   4. FORGOT PASSWORD
   ========================================================= */
const forgotPasswordForm = document.getElementById("forgotPasswordForm");

if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener("submit", async function(e) {
        e.preventDefault();

        const email = document.getElementById("forgotEmail")?.value.trim();

        if (!email) {
            showToast("Please enter your registered email", true);
            return;
        }

        try {
            const data = await api("/auth/forgot-password", {
                method: "POST",
                body: JSON.stringify({ email: email })
            });

            showToast(data.message || "Password reset link sent to your email");

            setTimeout(() => {
                window.location.href = "/login";
            }, 2000);

        } catch (error) {
            showToast(error.message || "Error sending reset link", true);
        }
    });
}

/* =========================================================
   5. RESET PASSWORD
   ========================================================= */
const resetPasswordForm = document.getElementById("resetPasswordForm");

if (resetPasswordForm) {
    resetPasswordForm.addEventListener("submit", async function(e) {
        e.preventDefault();

        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get("token");
        const newPassword = document.getElementById("newPassword")?.value;
        const confirmPassword = document.getElementById("confirmPassword")?.value;

        if (!token) {
            showToast("Invalid or missing reset token", true);
            return;
        }

        if (!newPassword || newPassword.length < 6) {
            showToast("Password must be at least 6 characters long", true);
            return;
        }

        if (newPassword !== confirmPassword) {
            showToast("Passwords do not match", true);
            return;
        }

        try {
            const data = await api("/auth/reset-password", {
                method: "POST",
                body: JSON.stringify({
                    token: token,
                    new_password: newPassword
                })
            });

            showToast(data.message || "Password reset successful! Redirecting...");

            setTimeout(() => {
                window.location.href = "/login";
            }, 1500);

        } catch (error) {
            showToast(error.message || "Failed to reset password", true);
        }
    });
}

/* =========================================================
   6. EMAIL VERIFICATION
   ========================================================= */
async function verifyEmailFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("token");

    if (token && window.location.pathname.includes("verify-email")) {
        try {
            const res = await api("/auth/verify-email", {
                method: "POST",
                body: JSON.stringify({ token: token })
            });
            showToast(res.message || "Email verified successfully!");
            setTimeout(() => {
                window.location.href = "/dashboard";
            }, 1500);
        } catch (error) {
            showToast(error.message || "Verification failed", true);
        }
    }
}

document.addEventListener("DOMContentLoaded", verifyEmailFromURL);

/* =========================================================
   7. TWO FACTOR AUTHENTICATION (2FA)
   ========================================================= */
const enable2FAForm = document.getElementById("enable2FAForm");
if (enable2FAForm) {
    enable2FAForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        try {
            const data = await api("/auth/2fa/enable", { method: "POST" });
            const qrContainer = document.getElementById("qrCodeContainer");
            if (qrContainer && data.qr_code) {
                qrContainer.innerHTML = `<img src="${data.qr_code}" alt="2FA QR Code" style="max-width:200px;"/>`;
            }
            showToast("Scan QR Code in Google Authenticator");
        } catch (error) {
            showToast(error.message, true);
        }
    });
}

const verify2FAForm = document.getElementById("verify2FAForm");
if (verify2FAForm) {
    verify2FAForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        const otp = document.getElementById("otpCode")?.value.trim();
        if (!otp) {
            showToast("Please enter 6-digit OTP", true);
            return;
        }
        try {
            const data = await api("/auth/2fa/verify", {
                method: "POST",
                body: JSON.stringify({ otp: otp })
            });
            showToast(data.message || "2FA Enabled Successfully!");
        } catch (error) {
            showToast(error.message || "Invalid OTP", true);
        }
    });
}