import React, { useState, useRef, useEffect } from 'react';
import { askQuestion, ChatResponse, Video } from './api';
import './ChatBox.css';

interface ChatBoxProps {
  video: Video | null;
}

export const ChatBox: React.FC<ChatBoxProps> = ({ video }) => {
  const [messages, setMessages] = useState<ChatResponse[]>([]);
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleAskQuestion = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!question.trim()) {
      alert('Please enter a question');
      return;
    }

    if (!video || video.transcription_status !== 'completed') {
      alert('Please select a transcribed video first');
      return;
    }

    setIsLoading(true);

    try {
      const response = await askQuestion(video.id, question);
      setMessages([...messages, response]);
      setQuestion('');
    } catch (error) {
      alert(`Failed to get answer: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chatbox-container">
      <h2>Ask a Question</h2>

      {!video || video.transcription_status !== 'completed' ? (
        <div className="chat-placeholder">
          <p>👈 Upload and transcribe a video to start asking questions</p>
        </div>
      ) : (
        <>
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="chat-placeholder">
                <p>Start by asking a question about the video</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className="message-group">
                  <div className="message question-msg">
                    <strong>You:</strong> {msg.question}
                  </div>
                  <div className="message answer-msg">
                    <strong>Assistant:</strong> {msg.answer}
                  </div>
                  {msg.source_chunks && msg.source_chunks.length > 0 && (
                    <div className="source-chunks">
                      <details>
                        <summary>📄 Source ({msg.source_chunks.length} chunks)</summary>
                        <div className="chunks-content">
                          {msg.source_chunks.map((chunk, idx) => (
                            <p key={idx} className="chunk-text">
                              {chunk.substring(0, 150)}...
                            </p>
                          ))}
                        </div>
                      </details>
                    </div>
                  )}
                </div>
              ))
            )}
            {isLoading && (
              <div className="message loading-msg">
                <p>⏳ Thinking...</p>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleAskQuestion} className="chat-form">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask something about the video..."
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading}>
              {isLoading ? 'Asking...' : 'Send'}
            </button>
          </form>
        </>
      )}
    </div>
  );
};
