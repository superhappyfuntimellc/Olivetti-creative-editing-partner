# 🔑 OpenAI API Key Setup

## Why You Need This

The **Story Bible**, **Import**, and all AI features require an OpenAI API key to work.

Without it, you'll see:
- ❌ Story Bible generation buttons don't work
- ❌ Import with AI processing fails
- ❌ All writing actions (Write, Rewrite, Expand, etc.) disabled
- ⚠️ "OPENAI_API_KEY not set" warnings

---

## Quick Setup (2 minutes)

### Step 1: Get Your API Key

1. Go to: https://platform.openai.com/api-keys
2. Sign in (or create account)
3. Click **"Create new secret key"**
4. Copy the key (starts with `sk-...`)

### Step 2: Add Key to Olivetti

**Option A: Edit secrets file (Recommended)**

Edit this file:
```
.streamlit/secrets.toml
```

Replace `"your-api-key-here"` with your actual key:
```toml
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxx"
```

**Option B: Environment variable**

```bash
export OPENAI_API_KEY="sk-proj-xxxxxxxxxxxx"
```

### Step 3: Restart Olivetti

```bash
pkill streamlit
streamlit run app.py
```

Or just reload the page - Streamlit will pick up the new secrets.

---

## Verify It's Working

After adding your key, you should see in the app:
- ✅ Story Bible generation buttons become active
- ✅ Import with AI processing works
- ✅ All writing action buttons enabled
- ✅ No "OPENAI_API_KEY not set" warnings

---

## Current Status

Run this to check configuration:
```bash
python3 -c "import os; print('✅ Key configured' if os.getenv('OPENAI_API_KEY') or open('.streamlit/secrets.toml').read().find('sk-') > 0 else '❌ No API key')"
```

---

## Troubleshooting

### "Invalid API key"
- Double-check you copied the full key (starts with `sk-`)
- Make sure there are no extra spaces
- Check your OpenAI account has credits/billing enabled

### Features still not working
- Hard refresh browser: `Ctrl+F5` or `Cmd+Shift+R`
- Clear browser cache
- Restart Streamlit completely

### Cost concerns
- GPT-4.1-mini is very affordable (~$0.15 per 1M tokens)
- Set usage limits in OpenAI dashboard
- Monitor usage at: https://platform.openai.com/usage

---

## Files Created for You

✅ `.streamlit/secrets.toml` - Add your API key here (recommended)  
✅ `.streamlit/config.toml` - App configuration  
✅ `credentials.toml` - Email config (no key needed here)

**Next step:** Edit `.streamlit/secrets.toml` and add your OpenAI API key!
