# Setting Up OpenUI with Ollama: Local Setup, Model Testing, and Troubleshooting

This guide walks through setting up OpenUI with Ollama locally, including model configuration, troubleshooting, and real-world notes from testing different local and cloud-hosted models.

This guide is beginner-friendly and walks through setting up OpenUI with Ollama step by step. Let's get started.

## Companion repo

[OpenUI + Ollama Local Setup Repo](https://github.com/shogun444/openui-ollama-localsetup)

---

## What You'll Need

Before we start, make sure you have these installed:

- **Node.js** - Download from [nodejs.org](https://nodejs.org/en/download)
- **Ollama** - Download from [ollama.com](https://ollama.com/download)
- **Git** - Download from [git-scm.com](https://git-scm.com/downloads)

**System Requirements:**

- 16GB RAM minimum (32GB recommended)
- 30GB free disk space
- Windows 10+, macOS 10.15+, or Linux

---

## Installing Ollama

Ollama is the tool that lets us run AI models locally. Here's how to set it up:

### Step 1: Download and Install Ollama

1. Go to [ollama.com/download](https://ollama.com/download)
2. Click the download button for your OS (Windows, Mac, or Linux)

<img src="../assets/Ollama.png" height="250px" />

3. After the setup is downloaded open it and press Install.

<img src="../assets/Installation.png" height="250px" />

4. When it's done, you should see the Ollama icon in your system tray. It means it has installed successfully.

<img src="../assets/Check.png" height="250px" />

You can also check by opening your terminal (Command Prompt on Windows, Terminal on Mac) and type:

```bash
ollama
```

You should see a list of available commands. This confirms Ollama installed correctly.

That's it for Ollama setup.

---

## Local Model Performance Notes

While testing OpenUI with Ollama, I noticed that smaller models (especially 3B–8B models) often had trouble generating stable UI layouts.

Common problems included:
- broken UI output,
- incomplete layouts,
- syntax errors,
- and inconsistent rendering.

Larger models like `qwen2.5-coder:14b` and `gpt-oss:20b` worked much better and produced more stable results, although they were slower on lower-memory systems.

In general, larger models handled OpenUI generation more reliably. Hosted models also produced the most consistent results during testing.

## Models Tested with OpenUI

During testing, different models behaved very differently when generating `openui-lang` output.

### Local Models

| Model | Result | Notes |
|---|---|---|
| `gpt-oss:20b` | Strong results | Produced significantly more stable layouts and fewer syntax issues, but inference was much slower on 16GB hardware. |
| `qwen2.5-coder:14b` | Mostly usable | Good local balance between quality and performance. Occasionally produced malformed or incomplete UI output. |
| `ministral-3:3b` | Unstable | Frequently generated incomplete or broken UI structures. |
| `phi4-mini:3.8b` | Unstable | Struggled with consistent structured generation. |


> Recommended:
> For better OpenUI results, larger models (generally 14B+ models) are recommended. They usually follow instructions more reliably and generate more stable UI layouts compared to smaller models.
>
> Smaller models may still work for simple prompts, but they often struggle with larger or more complex UI generation tasks.

### Cloud Models

Cloud-hosted models generally produced the most reliable OpenUI output during testing.

Models such as:
- `nemotron-3-super:cloud`
- `qwen3-next:80b-cloud`
- `gemma4:31b-cloud`

generated significantly more stable component trees and dashboard layouts compared to smaller local models.

> Note:
> Some cloud-hosted Ollama models may require subscriptions or gated access depending on provider policies and account availability.
>
> During testing, models such as `kimi-k2.5:cloud`, `minimax-m2.7:cloud`, and `glm-5.1:cloud` returned `403 subscription required` errors on some setups.

### 💡 Pro-Tip

You can find more models and details at the official [Ollama Search](https://ollama.com/search).

## Running OpenUI with Ollama Models

### Step 1: Pull a Model from Ollama

Before running OpenUI, pull a local Ollama model.

Example:

```bash
ollama run gpt-oss:20b
```

This downloads the model locally and starts the Ollama runtime.

You can verify installed models using:

```bash
ollama list
```

<img src="../assets/Ollama-list.png" height="250px" />



### Step 2: Create and Run an OpenUI App

Run the official OpenUI CLI:

```bash
npx @openuidev/cli@latest create --name genui-chat-app
cd genui-chat-app
```

This scaffolds a complete OpenUI chat application with:
- OpenUI Lang support,
- streaming UI generation,
- built-in components,
- and a ready-to-run Next.js setup.

### Create the `.env` File

On Windows PowerShell:

```powershell
New-Item .env -ItemType File
```

On Linux/macOS:

```bash
touch .env
```



Then add your configuration inside `.env`:

```env
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=gpt-oss:20b
```

You can replace the `OPENAI_MODEL` value with any Ollama local or cloud-hosted model.

### Step 4: Start the Development Server

```bash
npm run dev
```

Open:

```txt
http://localhost:3000
```

If everything is configured correctly, you should see the OpenUI chat interface running locally.

What this setup does:

- `OPENAI_BASE_URL` — Connects OpenUI to your local Ollama instance
- `OPENAI_MODEL` — Selects the Ollama model used for UI generation
- `npm run dev` — Starts the local Next.js development server

### Step 5: Test It

Open your browser to

```bash
http://localhost:3000
```

You should see the OpenUI chat interface
![OpenUI Chat](../assets/Openui-Chat.png)

Click any prompt shown on the screen.
If you get a response in the frontend, the setup is complete.

Try this prompt:
Create a contact form with name, email, and message fields
If a form appears, you're all set!

My Results:

![Minimal Calorie Tracker Dashboard](../assets/Calorie-Tracker.png)
![Simple Todo App](../assets/Simple-Todo.png)


## Using OpenRouter Hosted Models

You can also connect OpenUI to hosted models using OpenRouter instead of running models locally through Ollama.

This is useful if:
- your system does not have enough RAM for larger models,
- you want faster or more reliable generations,
- or you want to test larger hosted models without downloading them locally.

Models in the 27B–30B+ range generally followed instructions more reliably and handled larger UI generation tasks much better.

### Step 1: Create an OpenRouter API Key

1. Go to https://openrouter.ai
2. Create an account
3. Generate an API key from the dashboard

### Step 2: Update the `.env` File

Replace your local Ollama configuration with:

```env
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=your_openrouter_api_key
OPENAI_MODEL=google/gemma-3-27b-it
```

You can replace the `OPENAI_MODEL` value with any Ollama local or cloud-hosted model.

## Common Issues and Fixes

### `touch .env`  Not Working on Windows

**Problem:**

PowerShell does not recognize the `touch` command.

**Fix:**

Create the `.env` file manually or run:

```powershell
New-Item .env -ItemType File
```

---

### `404 model not found`

**Problem:**

The configured model does not exist in your Ollama installation.

**Fix:**

Check installed models:

```bash
ollama list
```

Then update the `MODEL` value inside `.env` with a valid installed model.

Example:

```env
OPENAI_MODEL=gpt-oss:20b 
```

---

### `403 subscription required`

**Problem:**

Some Ollama cloud-hosted models require subscriptions or gated access.

**Fix:**

Try another available cloud model or switch to a local model.

Examples tested during setup:

- `qwen2.5-coder:14b`
- `gpt-oss:20b`
- `nemotron-3-super:cloud`
- `gemma4:31b-cloud`
---

### `memory layout cannot be allocated`

**Problem:**

The selected model requires more RAM than your system can provide.

This commonly happens with larger models such as:
- `gemma4:26b`
- `glm-4.7-flash`

on lower-memory systems.

**Fix:**

- Use a smaller model
- Reduce context length
- Close other memory-heavy applications
- Use cloud-hosted models instead

---

### Blank Screen or Broken UI

**Problem:**

The model generated malformed `openui-lang` output.

This is more common with smaller local models.

**Fix:**

- Increase the Ollama context length
- Use a stronger model
- Retry the generation
- Prefer larger models for complex dashboards and layouts

---

### Increasing Context Length

Some local models performed significantly better after increasing the Ollama context length.

Example (Windows PowerShell):

```bash
setx OLLAMA_CONTEXT_LENGTH 8192
```

Restart your terminal after changing the value.

---

### React Rendering Errors

Example:

```txt
Objects are not valid as a React child
```

**Problem:**

The model generated an invalid component tree or malformed structured output.

**Fix:**

- Retry generation
- Use a stronger model
- Increase context length
- Avoid extremely small local models for complex UI generation

