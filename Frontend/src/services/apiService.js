/**
 * API Service for Git Link Analysis
 * Centralized API calls for analyzer functionality
 */

export const analyzeGitLink = async (gitLink) => {
  try {
    const response = await fetch('/api/chat/analyze-git-link/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ git_link: gitLink })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error analyzing git link:', error);
    throw error;
  }
};

export const quickAnalyzeRepo = async (gitLink) => {
  try {
    const response = await fetch('/api/chat/analyze-repo/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ git_link: gitLink })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error in quick analysis:', error);
    throw error;
  }
};

export const sendChatMessage = async (conversationId, message) => {
  try {
    const response = await fetch('/api/chat/send/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};
