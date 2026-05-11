import React, { useRef } from 'react';
interface AttachmentInputProps {
  onFilesSelected: (files: File[]) => void;
  acceptedTypes?: string;
}

export const AttachmentInput: React.FC<AttachmentInputProps> = ({
  onFilesSelected,
  acceptedTypes = 'image/*,video/*,text/*,.pdf,.xlsx,.csv',
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = React.useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onFilesSelected(files);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      onFilesSelected(files);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
        dragActive
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400'
      }`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={triggerFileInput}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={acceptedTypes}
        onChange={handleChange}
        className="hidden"
      />
      <div className="text-gray-600">
        <p className="font-medium">Drag files here or click to browse</p>
        <p className="text-sm text-gray-500">Images, videos, documents up to 20MB</p>
      </div>
    </div>
  );
};
