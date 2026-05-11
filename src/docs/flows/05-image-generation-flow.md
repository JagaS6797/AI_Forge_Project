# Flow 05: Image Generation in Chat

## Scope

End-to-end sequence for generating an image from chat input and rendering it as an assistant attachment.

## Actors

- InputBar (Generate Image mode)
- ChatWindow sendMessage mutation
- POST /api/chat stream
- image_generation_service
- file_attachments persistence

## Step-by-Step Flow (As Implemented)

1. User selects Generate Image mode and enters a prompt.
2. Frontend rewrites message to /image <prompt> if needed.
3. POST /api/chat starts SSE stream.
4. Chat service detects image-generation intent from message text.
5. Backend calls image provider using configured image_gen_model.
6. Backend receives b64_json or URL result and obtains image bytes.
7. Image bytes are saved through attachment service and metadata is persisted.
8. Backend streams token confirming image generation.
9. Backend streams attachment metadata event for the generated image.
10. Assistant message is persisted with generated attachment ID.
11. Stream completes with done=true.

## Failure Paths

- No usable image payload from provider -> streamed failure token.
- Provider timeout/network failure -> streamed failure token.
- Storage/persistence failure -> logged; stream still terminates safely.

## Error Handling

- OpenAI/provider exceptions are caught and converted to token + done stream events.
- Generic exceptions are caught and converted to user-visible error token + done event.
- Download/view endpoints enforce ownership and return 403/404 as appropriate.

## Enhancement Hooks

- Add image style presets and dimensions from frontend controls.
- Add progress events for long-running generation.
- Add moderation/classification gate before image is returned.
