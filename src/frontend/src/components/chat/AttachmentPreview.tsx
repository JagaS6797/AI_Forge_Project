import React from 'react';
import { X, File, Image, Video, Code } from 'lucide-react';

interface AttachmentPreviewProps {
  id: string;
  fileName: string;
  fileType: string;
  onRemove: (id: string) => void;
}

const getFileIcon = (fileType: string) => {
  if (fileType.startsWith('image/')) return <Image className="w-4 h-4" />;
  if (fileType.startsWith('video/')) return <Video className="w-4 h-4" />;
  if (fileType.includes('code') || fileType.includes('text/plain') || fileType.includes('javascript') || fileType.includes('python'))
    return <Code className="w-4 h-4" />;
  return <File className="w-4 h-4" />;
};

export const AttachmentPreview: React.FC<AttachmentPreviewProps> = ({
  id,
  fileName,
  fileType,
  onRemove,
}) => {
  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg text-sm">
      {getFileIcon(fileType)}
      <span className="truncate flex-1">{fileName}</span>
      <button
        onClick={() => onRemove(id)}
        className="p-0.5 hover:bg-gray-200 rounded transition-colors"
        type="button"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
