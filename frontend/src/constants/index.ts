export const SAMPLE_HTML = `<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
  <form id="login-form">
    <h1>Welcome back</h1>
    <label for="email">Email</label>
    <input id="email" type="email" name="email" placeholder="you@example.com" required />
    <label for="password">Password</label>
    <input id="password" type="password" name="password" placeholder="Your password" required />
    <a href="/forgot" class="forgot-link">Forgot password?</a>
    <button id="login-btn" type="submit" class="btn-primary">Sign In</button>
    <p class="signup-text">Don't have an account? <a href="/signup">Sign up</a></p>
  </form>
</body>
</html>`;
