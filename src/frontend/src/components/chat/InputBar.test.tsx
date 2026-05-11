import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ComponentProps } from "react";

import { InputBar } from "./InputBar";

function renderInputBar(overrides: Partial<ComponentProps<typeof InputBar>> = {}) {
  const props: ComponentProps<typeof InputBar> = {
    value: "",
    isSending: false,
    onChange: vi.fn(),
    onSubmit: vi.fn(),
    mode: "normal",
    onModeChange: vi.fn(),
    uploadedAttachments: [],
    onRemoveAttachment: vi.fn(),
    isUploading: false,
    hasRagDocument: false,
    ragEnabled: false,
    onRagToggle: vi.fn(),
    ...overrides,
  };

  render(<InputBar {...props} />);
  return props;
}

describe("InputBar", () => {
  it("submits when Enter is pressed without Shift", () => {
    const props = renderInputBar({ value: "Hello" });

    const textarea = screen.getByPlaceholderText(/Type a message/i);
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

    expect(props.onSubmit).toHaveBeenCalled();
  });

  it("does not submit when Shift+Enter is pressed", () => {
    const props = renderInputBar({ value: "Hello" });

    const textarea = screen.getByPlaceholderText(/Type a message/i);
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });

    expect(props.onSubmit).not.toHaveBeenCalled();
  });

  it("opens mode menu and triggers mode change", () => {
    const props = renderInputBar();

    fireEvent.click(screen.getByTitle("Select chat mode"));
    fireEvent.click(screen.getByText("Generate Image"));

    expect(props.onModeChange).toHaveBeenCalledWith("generate_image");
  });

  it("send button is disabled when message and attachments are empty", () => {
    renderInputBar({ value: "   ", uploadedAttachments: [] });

    const sendButton = screen.getByTitle("Send message");
    expect(sendButton).toBeDisabled();
  });

  it("send button is enabled when there is an attachment-only request", () => {
    renderInputBar({
      value: "",
      uploadedAttachments: [
        {
          id: "att-1",
          file_name: "notes.txt",
          file_type: "text/plain",
          file_size: 10,
          created_at: "2026-01-01T00:00:00Z",
        },
      ],
    });

    const sendButton = screen.getByTitle("Send message");
    expect(sendButton).not.toBeDisabled();
  });
});
