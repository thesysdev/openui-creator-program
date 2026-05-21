# LiveKit + OpenUI shared screen demo

This companion demo backs the article "Voice Agents Need a Shared Screen."

It is intentionally small: the example simulates a LiveKit voice-agent turn,
streams OpenUI-style visual frames, marks older turns as stale, and routes
button clicks through an application-owned action registry.

## Files

- `shared-screen-demo.ts`: the TypeScript-shaped state and action model behind
  the article examples.
- `index.html`: a static visual demo used to capture the article screenshots.

## Run locally

Open `index.html` in a browser. Use the buttons at the top to switch between
the ready state, the interruption/updating state, and the tool-failure recovery
state.

In a production implementation, the static state transitions shown here would
be driven by LiveKit room/agent events and streamed OpenUI frames.
