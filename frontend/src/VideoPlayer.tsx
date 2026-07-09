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
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title || !instructorId) {
      setErrorMessage('Please fill in all fields before uploading.');
      return;
    }

    setErrorMessage('');
    setIsUploading(true);
    setUploadProgress(0);

    try {
      const video = await uploadVideo(file, title, instructorId, setUploadProgress);
      onVideoLoaded(video);
      setFile(null);
      setTitle('');
      setInstructorId('');
    } catch (error) {
      setErrorMessage(`Upload failed: ${error}`);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="video-player-container">
      <h2>Upload Course Video</h2>

      {currentVideo ? (
        <div className="video-info">
          <p>
            <span className="info-label">Title</span>
            {currentVideo.title}
          </p>
          <p>
            <span className="info-label">Status</span>
            <span className={`status-pill status-${currentVideo.transcription_status}`}>
              {currentVideo.transcription_status}
            </span>
          </p>
          {currentVideo.transcription_status === 'pending' && (
            <div className="info-message">
              <span className="spinner" aria-hidden="true" />
              Transcribing&hellip; this typically takes 2-5 minutes
            </div>
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
            <label htmlFor="video-title">Video Title</label>
            <input
              id="video-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Intro to Python Lesson 1"
              disabled={isUploading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="instructor-id">Instructor ID (UUID)</label>
            <input
              id="instructor-id"
              type="text"
              value={instructorId}
              onChange={(e) => setInstructorId(e.target.value)}
              placeholder="550e8400-e29b-41d4-a716-446655440000"
              disabled={isUploading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="video-file">Select Video File</label>
            <input
              id="video-file"
              type="file"
              accept="video/*"
              onChange={handleFileSelect}
              disabled={isUploading}
            />
            {file && !isUploading && (
              <p className="file-info">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <path d="M14 2v6h6" />
                </svg>
                {file.name}
              </p>
            )}
          </div>

          {isUploading && (
            <div className="progress-wrap" role="progressbar" aria-valuenow={uploadProgress} aria-valuemin={0} aria-valuemax={100}>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
              </div>
              <span className="progress-label">
                {uploadProgress < 100 ? `Uploading… ${uploadProgress}%` : 'Processing…'}
              </span>
            </div>
          )}

          <button type="submit" disabled={isUploading} className="primary-button">
            {isUploading ? 'Uploading…' : 'Upload & Transcribe'}
          </button>

          {errorMessage && <p className="error-message">{errorMessage}</p>}
        </form>
      )}
    </div>
  );
};
