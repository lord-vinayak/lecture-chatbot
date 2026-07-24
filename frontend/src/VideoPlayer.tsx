import React, { useEffect, useState } from 'react';
import {
  Video,
  uploadVideo,
  submitYoutubeVideo,
  listVideos,
  deleteVideo,
  getVideoUrl,
  getYoutubeEmbedUrl,
  extractYoutubeId,
} from './api';
import './VideoPlayer.css';

interface VideoPlayerProps {
  onVideoLoaded: (video: Video) => void;
  onBack: () => void;
  currentVideo: Video | null;
}

// crypto.randomUUID() requires a secure context (HTTPS/localhost); this works everywhere
const generateUUID = (): string =>
  'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  onVideoLoaded,
  onBack,
  currentVideo,
}) => {
  const [sourceMode, setSourceMode] = useState<'upload' | 'youtube'>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [title, setTitle] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [videos, setVideos] = useState<Video[]>([]);

  const refreshVideoList = () => {
    listVideos()
      .then(setVideos)
      .catch(() => setVideos([]));
  };

  useEffect(() => {
    refreshVideoList();
  }, []);

  const handleDelete = async (e: React.MouseEvent, video: Video) => {
    e.stopPropagation();
    if (!window.confirm(`Delete "${video.title}"? This can't be undone.`)) return;

    try {
      await deleteVideo(video.id);
      refreshVideoList();
      if (currentVideo?.id === video.id) onBack();
    } catch (error) {
      setErrorMessage(`Delete failed: ${error}`);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (sourceMode === 'youtube') {
      if (!youtubeUrl || !title) {
        setErrorMessage('Please fill in all fields before submitting.');
        return;
      }
      if (!extractYoutubeId(youtubeUrl)) {
        setErrorMessage('Please enter a valid YouTube URL.');
        return;
      }

      setErrorMessage('');
      setIsUploading(true);

      try {
        const video = await submitYoutubeVideo(youtubeUrl, title, generateUUID());
        onVideoLoaded(video);
        refreshVideoList();
        setYoutubeUrl('');
        setTitle('');
      } catch (error) {
        setErrorMessage(`Submission failed: ${error}`);
      } finally {
        setIsUploading(false);
      }
      return;
    }

    if (!file || !title) {
      setErrorMessage('Please fill in all fields before uploading.');
      return;
    }

    setErrorMessage('');
    setIsUploading(true);
    setUploadProgress(0);

    try {
      const video = await uploadVideo(file, title, generateUUID(), setUploadProgress);
      onVideoLoaded(video);
      refreshVideoList();
      setFile(null);
      setTitle('');
    } catch (error) {
      setErrorMessage(`Upload failed: ${error}`);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="video-player-container">
      {currentVideo ? (
        <div className="video-detail-scroll">
          <div className="video-player-header">
            <h2>{currentVideo.title}</h2>
            <button type="button" className="link-button" onClick={onBack}>
              &larr; Back to videos
            </button>
          </div>

          {currentVideo.source_type === 'youtube' ? (
            <iframe
              key={currentVideo.id}
              className="video-player"
              src={getYoutubeEmbedUrl(currentVideo)}
              title={currentVideo.title}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          ) : (
            <video
              key={currentVideo.id}
              className="video-player"
              src={getVideoUrl(currentVideo)}
              controls
              preload="metadata"
            />
          )}

          <div className="video-info">
            <p>
              <span className="info-label">Status</span>
              <span className={`status-pill status-${currentVideo.transcription_status}`}>
                {currentVideo.transcription_status}
              </span>
            </p>
            {currentVideo.transcription_status === 'pending' && (
              <div className="progress-wrap" role="progressbar" aria-valuenow={currentVideo.transcription_progress} aria-valuemin={0} aria-valuemax={100}>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: `${currentVideo.transcription_progress}%` }} />
                </div>
                <span className="progress-label">
                  <span className="spinner" aria-hidden="true" /> Transcribing&hellip; {currentVideo.transcription_progress}%
                </span>
              </div>
            )}
            {currentVideo.transcription_status === 'failed' && (
              <p className="error-message">
                Transcription failed. Check audio quality and try again.
              </p>
            )}
          </div>
        </div>
      ) : (
        <>
          <div className="upload-section">
          <h2>Upload Course Video</h2>

          <form onSubmit={handleUpload} className="upload-form">
            <div className="form-group source-toggle" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={sourceMode === 'upload'}
                className={`toggle-button ${sourceMode === 'upload' ? 'active' : ''}`}
                onClick={() => setSourceMode('upload')}
                disabled={isUploading}
              >
                Upload File
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={sourceMode === 'youtube'}
                className={`toggle-button ${sourceMode === 'youtube' ? 'active' : ''}`}
                onClick={() => setSourceMode('youtube')}
                disabled={isUploading}
              >
                YouTube Link
              </button>
            </div>

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

            {sourceMode === 'upload' ? (
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
            ) : (
              <div className="form-group">
                <label htmlFor="video-youtube-url">YouTube URL</label>
                <input
                  id="video-youtube-url"
                  type="url"
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  disabled={isUploading}
                />
              </div>
            )}

            {isUploading && sourceMode === 'upload' && (
              <div className="progress-wrap" role="progressbar" aria-valuenow={uploadProgress} aria-valuemin={0} aria-valuemax={100}>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
                </div>
                <span className="progress-label">
                  {uploadProgress < 100 ? `Uploading… ${uploadProgress}%` : 'Processing…'}
                </span>
              </div>
            )}

            {isUploading && sourceMode === 'youtube' && (
              <p className="progress-label">Submitting…</p>
            )}

            <button type="submit" disabled={isUploading} className="primary-button">
              {isUploading
                ? sourceMode === 'youtube' ? 'Submitting…' : 'Uploading…'
                : sourceMode === 'youtube' ? 'Submit & Transcribe' : 'Upload & Transcribe'}
            </button>

            {errorMessage && <p className="error-message">{errorMessage}</p>}
          </form>
          </div>

          {videos.length > 0 && (
            <div className="video-list-scroll">
              <h3>Previous Videos</h3>
              <div className="video-list">
                {videos.map((v) => (
                  <div key={v.id} className="video-list-item">
                    <button
                      type="button"
                      className="video-list-item-main"
                      onClick={() => onVideoLoaded(v)}
                    >
                      <span className="video-list-title">{v.title}</span>
                      <span className={`status-pill status-${v.transcription_status}`}>
                        {v.transcription_status}
                      </span>
                    </button>
                    <button
                      type="button"
                      aria-label={`Delete ${v.title}`}
                      className="delete-button"
                      onClick={(e) => handleDelete(e, v)}
                    >
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 6h18" />
                        <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
