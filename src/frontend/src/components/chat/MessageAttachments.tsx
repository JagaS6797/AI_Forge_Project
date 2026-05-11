import { useState, useEffect } from "react";
import { Download, File, Image, Video, Code, X } from "lucide-react";
import type { ChatAttachment } from "../../types";

type MessageAttachmentsProps = {
  attachments?: ChatAttachment[];
  messageRole: "user" | "assistant";
};

type ImageCache = { [key: string]: string };

export function MessageAttachments({
  attachments,
  messageRole,
}: MessageAttachmentsProps) {
  const [expandedImageId, setExpandedImageId] = useState<string | null>(null);
  const [imageUrls, setImageUrls] = useState<ImageCache>({});
  const [loadingImages, setLoadingImages] = useState<Set<string>>(new Set());

  if (!attachments || attachments.length === 0) return null;

  // Load image previews with authentication
  useEffect(() => {
    const imageAttachments = attachments.filter((a) =>
      a.file_type.startsWith("image/")
    );

    imageAttachments.forEach((attachment) => {
      if (!imageUrls[attachment.id] && !loadingImages.has(attachment.id)) {
        setLoadingImages((prev) => new Set(prev).add(attachment.id));
        
        fetch(`/api/chat/attachments/${attachment.id}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("amzur_chat_access_token") || ""}`,
          },
        })
          .then((response) => {
            if (!response.ok) throw new Error("Failed to load image");
            return response.blob();
          })
          .then((blob) => {
            const url = URL.createObjectURL(blob);
            setImageUrls((prev) => ({ ...prev, [attachment.id]: url }));
          })
          .catch((error) => {
            console.error(`Failed to load image ${attachment.file_name}:`, error);
          })
          .finally(() => {
            setLoadingImages((prev) => {
              const next = new Set(prev);
              next.delete(attachment.id);
              return next;
            });
          });
      }
    });

    return () => {
      // Cleanup object URLs on unmount
      Object.values(imageUrls).forEach((url) => URL.revokeObjectURL(url));
    };
  }, [attachments]);

  const getFileIcon = (fileType: string) => {
    if (fileType.startsWith("image/")) return <Image className="h-4 w-4" />;
    if (fileType.startsWith("video/")) return <Video className="h-4 w-4" />;
    if (
      fileType.includes("javascript") ||
      fileType.includes("typescript") ||
      fileType.includes("python") ||
      fileType.includes("code")
    )
      return <Code className="h-4 w-4" />;
    return <File className="h-4 w-4" />;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleDownload = async (attachment: ChatAttachment) => {
    try {
      const response = await fetch(`/api/chat/attachments/${attachment.id}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("amzur_chat_access_token") || ""}`,
        },
      });
      if (!response.ok) throw new Error("Download failed");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = attachment.file_name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download error:", error);
      alert("Failed to download attachment");
    }
  };

  // Separate images from other attachments
  const imageAttachments = attachments.filter((a) => a.file_type.startsWith("image/"));
  const otherAttachments = attachments.filter((a) => !a.file_type.startsWith("image/"));

  return (
    <div className="mt-3 flex flex-col gap-3">
      {/* Image previews */}
      {imageAttachments.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {imageAttachments.map((attachment) => {
            const isExpanded = expandedImageId === attachment.id;
            const imageUrl = imageUrls[attachment.id];
            const isLoading = loadingImages.has(attachment.id);

            return (
              <div key={attachment.id} className="relative group">
                {/* Thumbnail */}
                <button
                  onClick={() => setExpandedImageId(isExpanded ? null : attachment.id)}
                  className="relative h-16 w-16 rounded-lg overflow-hidden border border-slate-300 hover:border-slate-400 transition bg-slate-100 flex items-center justify-center"
                  title={attachment.file_name}
                  disabled={isLoading}
                >
                  {imageUrl ? (
                    <img
                      src={imageUrl}
                      alt={attachment.file_name}
                      className="h-full w-full object-cover"
                    />
                  ) : isLoading ? (
                    <div className="animate-spin">
                      <Image className="h-5 w-5 text-slate-400" />
                    </div>
                  ) : (
                    <Image className="h-5 w-5 text-slate-400" />
                  )}
                </button>

                {/* Expanded view */}
                {isExpanded && imageUrl && (
                  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
                    <div className="relative max-w-2xl max-h-[80vh] bg-white rounded-lg overflow-hidden shadow-lg">
                      <button
                        onClick={() => setExpandedImageId(null)}
                        className="absolute top-2 right-2 p-1 bg-white/90 rounded hover:bg-white z-10"
                      >
                        <X className="h-5 w-5" />
                      </button>
                      <img
                        src={imageUrl}
                        alt={attachment.file_name}
                        className="max-w-full max-h-[80vh] object-contain"
                      />
                      <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
                        <div className="text-xs text-slate-600 truncate">
                          {attachment.file_name} ({formatFileSize(attachment.file_size)})
                        </div>
                        <button
                          onClick={() => handleDownload(attachment)}
                          className="p-1 hover:bg-slate-200 rounded transition"
                        >
                          <Download className="h-4 w-4 text-slate-600" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Other attachments as chips */}
      {otherAttachments.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {otherAttachments.map((attachment) => (
            <button
              key={attachment.id}
              onClick={() => handleDownload(attachment)}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                messageRole === "user"
                  ? "bg-indigo-500/20 text-indigo-200 hover:bg-indigo-500/30"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
              title={`${attachment.file_name} (${formatFileSize(attachment.file_size)})`}
            >
              {getFileIcon(attachment.file_type)}
              <span className="truncate max-w-[120px]">{attachment.file_name}</span>
              <Download className="h-3 w-3 opacity-60" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
