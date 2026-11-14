import React, { useState } from 'react';
import { Send } from 'lucide-react';
import { VoiceWidget } from './VoiceWidget';

interface TextFallbackProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
  role: string;
}

export const TextFallback: React.FC<TextFallbackProps> = ({ onSendMessage, disabled, role }) => {
  const [inputText, setInputText] = useState('');

  const suggestions: Record<string, string[]> = {
    public: [
      "Tell me about KIT",
      "What courses do you offer?",
      "What are the admission requirements?",
      "Show holidays",
      "What is the minimum attendance requirement?"
    ],
    student: [
      "Show my attendance",
      "Show my timetable",
      "I need leave",
      "Apply for on duty",
      "Show my requests"
    ],
    teacher: [
      "Show pending requests",
      "Approve request REQ-9012",
      "Reject request REQ-9015",
      "Show holidays"
    ]
  };

  const currentSuggestions = suggestions[role] || suggestions.public;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || disabled) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  return (
    <div className="controls-bar">
      {/* Suggestion Pills */}
      <div className="pills-container">
        {currentSuggestions.map((pill, i) => (
          <button
            key={i}
            className="pill-btn"
            onClick={() => onSendMessage(pill)}
            disabled={disabled}
          >
            {pill}
          </button>
        ))}
      </div>

      {/* Input Row */}
      <form onSubmit={handleSubmit} className="input-row">
        <VoiceWidget
          onSpeechRecognized={(phrase) => onSendMessage(phrase)}
          disabled={disabled}
        />
        <input
          type="text"
          className="text-input"
          placeholder="Speak using the microphone or type any supported command..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={disabled}
        />
        <button type="submit" className="send-btn" disabled={disabled || !inputText.trim()}>
          <Send size={18} />
        </button>
      </form>
    </div>
  );
};

