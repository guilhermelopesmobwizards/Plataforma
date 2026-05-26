<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Access Denied — MAP Control</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0f1117;
    --surface: #181c27;
    --surface2: #1e2336;
    --border: rgba(255,255,255,0.07);
    --border2: rgba(255,255,255,0.12);
    --text: #e8eaf0;
    --muted: #6b7280;
    --accent: #6366f1;
    --danger: #ef4444;
    --font-body: 'Inter', system-ui, -apple-system, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
    --radius: 6px;
    --radius-lg: 10px;
  }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-body);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--border2);
    border-radius: var(--radius-lg);
    padding: 48px 56px;
    width: 480px;
    max-width: 95vw;
    text-align: center;
  }
  .icon {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: rgba(239,68,68,0.1);
    border: 1px solid rgba(239,68,68,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 24px;
  }
  h1 {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 10px;
    color: var(--text);
  }
  p {
    font-size: 13px;
    color: var(--muted);
    line-height: 1.6;
    margin-bottom: 8px;
  }
  .email {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text);
    background: var(--surface2);
    border: 1px solid var(--border2);
    border-radius: var(--radius);
    padding: 4px 10px;
    display: inline-block;
    margin-bottom: 28px;
  }
  .divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 28px 0;
  }
  .countdown-text {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 16px;
  }
  .countdown-text span {
    font-family: var(--font-mono);
    color: var(--accent);
    font-weight: 600;
  }
  .progress-bar {
    height: 3px;
    background: var(--surface2);
    border-radius: 99px;
    overflow: hidden;
    margin-bottom: 20px;
  }
  .progress-fill {
    height: 100%;
    background: var(--accent);
    width: 100%;
    transition: width 1s linear;
  }
  .btn {
    display: inline-block;
    padding: 9px 20px;
    border-radius: var(--radius);
    font-size: 12px;
    font-family: var(--font-body);
    font-weight: 500;
    cursor: pointer;
    border: 1px solid var(--border2);
    background: var(--surface2);
    color: var(--text);
    text-decoration: none;
  }
  .btn:hover { background: var(--surface); }
  .wordmark {
    font-size: 11px;
    color: var(--muted);
    margin-bottom: 32px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
</style>
</head>
<body>
<div class="card">
  <div class="wordmark">MAP Control</div>
  <div class="icon">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
      <path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="#ef4444" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </div>
  <h1>Access Denied</h1>
  <p>Your account doesn't have permission to access the admin panel.</p>
  {% if user.email %}
  <div class="email">{{ user.email }}</div>
  {% endif %}
  <p>Contact an administrator if you believe this is a mistake.</p>
  <hr class="divider">
  <div class="countdown-text">Redirecting to dashboard in <span id="count">5</span>s</div>
  <div class="progress-bar"><div class="progress-fill" id="bar"></div></div>
  <a href="{{ redirect_url }}" class="btn">Go to Dashboard now</a>
</div>
<script>
  let n = {{ countdown }};
  const count = document.getElementById("count");
  const bar = document.getElementById("bar");
  // Start animation on next frame so transition fires
  requestAnimationFrame(() => {
    bar.style.width = "0%";
    bar.style.transitionDuration = n + "s";
  });
  const tick = setInterval(() => {
    n--;
    count.textContent = n;
    if (n <= 0) { clearInterval(tick); location.href = "{{ redirect_url }}"; }
  }, 1000);
</script>
</body>
</html>
