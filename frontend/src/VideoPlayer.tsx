import React, { useState } from 'react';
import { Video, uploadVideo } from './api';
import './VideoPlayer.css';

interface VideoPlayerProps {
  onVideoLoaded: (video: Video) => void;
  currentVideo: Video | null;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  onVideoLoaded,
  currentVideo,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [instructorId, setInstructorId] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title || !instructorId) {
      alert('Please fill in all fields');
      return;
    }

    setIsUploading(true);
    setUploadProgress('Uploading...');

    try {
      const video = await uploadVideo(file, title, instructorId);
      onVideoLoaded(video);
      setFile(null);
      setTitle('');
      setInstructorId('');
      setUploadProgress('');
    } catch (error) {
      setUploadProgress(`Upload failed: ${error}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="video-player-container">
      <h2>Upload Course Video</h2>

      {currentVideo ? (
        <div className="video-info">
          <p>
            <strong>Title:</strong> {currentVideo.title}
          </p>
          <p>
            <strong>Status:</strong> {currentVideo.transcription_status}
          </p>
          {currentVideo.transcription_status === 'pending' && (
            <p className="info-message">
              Transcribing... Please wait (typically 2-5 minutes)
            </p>
          )}
          {currentVideo.transcription_status === 'failed' && (
            <p className="error-message">
              Transcription failed. Check audio quality and try again.
            </p>
          )}
        </div>
      ) : (
        <form onSubmit={handleUpload} className="upload-form">
          <div className="form-group">
            <label>Video Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Intro to Python Lesson 1"
              disabled={isUploading}
            />
          </div>

          <div className="form-group">
            <label>Instructor ID (UUID)</label>
            <input
              type="text"
              value={instructorId}
              onChange={(e) => setInstructorId(e.target.value)}
              placeholder="550e8400-e29b-41d4-a716-446655440000"
              disabled={isUploading}
            />
          </div>

          <div className="form-group">
            <label>Select Video File</label>
            <input
              type="file"
              accept="video/*"
              onChange={handleFileSelect}
              disabled={isUploading}
            />
            {file && <p className="file-info">Selected: {file.name}</p>}
          </div>

          <button type="submit" disabled={isUploading}>
            {isUploading ? 'Uploading...' : 'Upload & Transcribe'}
          </button>

          {uploadProgress && <p className="upload-status">{uploadProgress}</p>}
        </form>
      )}
    </div>
  );
};
