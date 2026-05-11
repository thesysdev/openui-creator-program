# OpenUI's React Renderer Explained: How Progressive Rendering Works with Streamed Model Output

When people first see Generative UI, it is easy to imagine the model returning a complete JSON object, the app parsing it, and React rendering the result in one pass.

OpenUI takes a different approach.

Instead of treating model output as plain text or waiting for a fully completed JSON payload, OpenUI uses **OpenUI Lang**: a compact, streaming-first language for model-generated interfaces. The model emits structured UI text, and the React `Renderer` turns that streamed response into a live component tree.

The practical result is simple: users do not have to wait for the entire response before the interface starts taking shape. The UI can progressively become visible and useful while the model is still generating.

This article explains how that flow works, why it is different from ordinary JSON rendering, and what tradeoffs developers should understand before building on it.

---

## The basic OpenUI pipeline

At a high level, OpenUI turns a component library into a language model contract.

The app defines which components are available. OpenUI uses that library to generate instructions for the model. The model then responds in OpenUI Lang, and the client-side renderer parses that response into React UI.
```text
Component Library
      ↓
System Prompt
      ↓
LLM
      ↓
OpenUI Lang Stream
      ↓
Renderer
      ↓
Live React UI
```