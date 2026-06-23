import { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import LandingPage from './LandingPage';
import LoginModal from './LoginModal';
import MarkdownRenderer from './MarkdownRenderer';
import ConfirmDialog from './ConfirmDialog';

// Recursive File Tree Node component
function FileTreeNode({ node, path, collapsedNodes, onToggle, onFileClick }) {
  const isFolder = node.type === 'folder';
  const hasChildren = isFolder && node.children && node.children.length > 0;
  const isCollapsed = collapsedNodes[path] === true;

  const handleToggle = (e) => {
    if (isFolder) {
      onToggle(path);
    } else {
      if (onFileClick) onFileClick(path);
    }
  };

  return (
    <div className="tree-node">
      <div 
        className={`tree-row ${!isFolder ? 'tree-row-file' : ''}`} 
        onClick={handleToggle}
      >
        {isFolder ? (
          <span className={`tree-arrow ${!isCollapsed ? 'expanded' : ''}`}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          </span>
        ) : (
          <span style={{ width: '10px' }}></span>
        )}
        
        <span className="tree-icon">
          {isFolder ? (
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#2D6A4F' }}><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/></svg>
          ) : (
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#6E6E6E' }}><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>
          )}
        </span>
        
        <span className="tree-name" style={{ marginLeft: '4px' }}>{node.name}</span>
        
        {!isFolder && node.size && (
          <span className="tree-size">{node.size}</span>
        )}
      </div>
      
      {isFolder && hasChildren && !isCollapsed && (
        <div className="tree-children">
          {node.children.map((child, idx) => {
            const childPath = `${path}/${child.name}`;
            return (
              <FileTreeNode 
                key={idx} 
                node={child} 
                path={childPath} 
                collapsedNodes={collapsedNodes} 
                onToggle={onToggle}
                onFileClick={onFileClick}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

function App() {
  // Authentication states
  const [user, setUser] = useState(null);
  const [authProvider, setAuthProvider] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);
  const [loginModalOpen, setLoginModalOpen] = useState(false);

  // Conversations history states
  const [conversations, setConversations] = useState([]);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  // Chat message input state
  const [messageInput, setMessageInput] = useState('');
  const [aiTyping, setAiTyping] = useState(false);

  // Connected repository states for active conversation
  const [connectedRepo, setConnectedRepo] = useState(null);
  const canPerformWriteActions = connectedRepo?.source === 'github_owned' && user?.has_full_agent_access === true;
  const [explicitRepoId, setExplicitRepoId] = useState(null); // Only repos explicitly connected via UI
  const [userGithubUsername, setUserGithubUsername] = useState(null);

  const [applyFixFilePath, setApplyFixFilePath] = useState('');
  const [applyFixDescription, setApplyFixDescription] = useState('');
  const [applyFixDialogOpen, setApplyFixDialogOpen] = useState(false);
  const [applyFixLoading, setApplyFixLoading] = useState(false);

  const [reviewingMsgId, setReviewingMsgId] = useState(null);
  const [reviewPrNumber, setReviewPrNumber] = useState('');
  const [reviewPrLoading, setReviewPrLoading] = useState(false);

  const extractFilePath = (text) => {
    let match = text.match(/FILE:\s*([^\s\n\r]+)/i);
    if (match) return match[1].replace(/[`'"*]/g, '').trim();

    match = text.match(/`([^`\n\r]+\.(?:py|js|jsx|ts|tsx|css|html|json|sh|yml|md|rb|go|php|java))`/);
    if (match) return match[1].trim();

    return '';
  };

  // Helper function to save messages to database (for PR, bug hunt, review messages)
  const saveToDatabaseAsync = async (conversationId, messageText) => {
    if (!conversationId) return;
    try {
      await fetch(`/api/chat/conversations/${conversationId}/save-message/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText })
      });
    } catch (err) {
      console.error('Failed to save message to database:', err);
    }
  };

  const handleApplyFixAndOpenPR = async (filePath, desc) => {
    if (!connectedRepo || !filePath.trim() || !desc.trim()) return;
    setApplyFixLoading(true);
    setApplyFixDialogOpen(false);

    // Add a loading message to the chat
    const loadingMsgId = Date.now();
    setMessages(prev => [...prev, {
      id: loadingMsgId,
      sender: 'assistant',
      text: `🔧 Applying the fix to \`${filePath}\` and creating a pull request...`,
      is_system_loading: true
    }]);

    try {
      const response = await fetch(`/api/repos/${connectedRepo.id}/apply-fix/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: filePath.trim(),
          description: desc.trim()
        })
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Failed to apply fix and open PR.');
      }

      // Add PR success message
      const prMessageText = `✅ Opened pull request: [PR #${data.pr_number} - View on GitHub](${data.pr_url})\n\n**Change Summary:** ${data.summary_of_change}`;
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMsgId);
        return [...filtered, {
          id: Date.now(),
          sender: 'assistant',
          text: prMessageText,
          created_at: new Date().toISOString()
        }];
      });
      // Save to database
      saveToDatabaseAsync(activeConversation?.id, prMessageText);
    } catch (err) {
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMsgId);
        return [...filtered, {
          id: Date.now(),
          sender: 'assistant',
          text: `⚠️ **Apply Fix Error:** ${err.message}`
        }];
      });
    } finally {
      setApplyFixLoading(false);
    }
  };

  const handleReviewPRSubmit = async (prNum) => {
    if (!connectedRepo || !prNum.trim()) return;
    setReviewPrLoading(true);
    setReviewingMsgId(null); // Close input area

    // Add a loading message to the chat
    const loadingMsgId = Date.now();
    setMessages(prev => [...prev, {
      id: loadingMsgId,
      sender: 'assistant',
      text: `🔍 Reviewing Pull Request #${prNum}...`,
      is_system_loading: true
    }]);

    try {
      const response = await fetch(`/api/repos/${connectedRepo.id}/review-pr/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pr_number: parseInt(prNum, 10)
        })
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Failed to review pull request.');
      }

      // Add Review text message
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMsgId);
        return [...filtered, {
          id: Date.now(),
          sender: 'assistant',
          text: data.review,
          created_at: new Date().toISOString()
        }];
      });
      // Save to database
      saveToDatabaseAsync(activeConversation?.id, data.review);
    } catch (err) {
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMsgId);
        return [...filtered, {
          id: Date.now(),
          sender: 'assistant',
          text: `⚠️ **PR Review Error:** ${err.message}`
        }];
      });
    } finally {
      setReviewPrLoading(false);
      setReviewPrNumber('');
    }
  };

  // Connect popover details
  const [connectPopoverOpen, setConnectPopoverOpen] = useState(false);
  const [githubRepos, setGithubRepos] = useState([]);
  const [loadingGithubRepos, setLoadingGithubRepos] = useState(false);
  const [githubSearch, setGithubSearch] = useState('');
  const [githubDropdownOpen, setGithubDropdownOpen] = useState(false);
  const [selectedGithubRepo, setSelectedGithubRepo] = useState(null);
  const [pastedUrl, setPastedUrl] = useState('');
  const [connectLoading, setConnectLoading] = useState(false);
  const [connectStep, setConnectStep] = useState('');
  const [connectError, setConnectError] = useState(null);

  // Summary and file tree cards expanded toggling
  const [showSummaryBannerCard, setShowSummaryBannerCard] = useState(false);
  const [collapsedNodes, setCollapsedNodes] = useState({});

  // Bug Hunt & Code Review states
  const [bugHuntLoading, setBugHuntLoading] = useState(false);
  const [codeReviewLoading, setCodeReviewLoading] = useState(false);
  const [autoFixPRLoading, setAutoFixPRLoading] = useState(false);

  // Editor Modal states
  const [editorOpen, setEditorOpen] = useState(false);
  const [editorFile, setEditorFile] = useState('');
  const [editorContent, setEditorContent] = useState('');
  const [editorLoading, setEditorLoading] = useState(false);
  const [editorSaving, setEditorSaving] = useState(false);
  const [editorError, setEditorError] = useState(null);

  // Responsive mobile states
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // Dialog states for confirmations
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteConversationId, setDeleteConversationId] = useState(null);
  const [prConfirmDialogOpen, setPrConfirmDialogOpen] = useState(false);

  // Textarea and messages scrolling refs
  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);
  const popoverRef = useRef(null);

  // Scroll to bottom of chat list
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, aiTyping]);

  // Handle clicking outside the popover to close it
  useEffect(() => {
    function handleClickOutside(event) {
      if (popoverRef.current && !popoverRef.current.contains(event.target)) {
        setConnectPopoverOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch user session on page mount
  useEffect(() => {
    async function checkAuth() {
      // -----------------------------------------------------------
      // Cross-domain OAuth token handoff:
      // After OAuth, the backend redirects here with ?auth_token=xxx
      // Exchange it for a real session first.
      // -----------------------------------------------------------
      const params = new URLSearchParams(window.location.search);
      const authToken = params.get('auth_token');

      if (authToken) {
        // Clean the token from the URL immediately
        window.history.replaceState({}, document.title, window.location.pathname);
        try {
          const tokenRes = await fetch('/api/auth/token-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ token: authToken }),
          });
          if (tokenRes.ok) {
            const tokenData = await tokenRes.json();
            if (tokenData.user) {
              setUser(tokenData.user);
              setAuthProvider(tokenData.user.auth_provider);
              if (tokenData.user.github_username) {
                setUserGithubUsername(tokenData.user.github_username);
              }
              setLoadingUser(false);
              return; // Done – skip the /api/auth/me fallback
            }
          }
        } catch (tokenErr) {
          console.error('Token login failed, falling back to session check:', tokenErr);
        }
      }

      // -----------------------------------------------------------
      // Normal session-based auth check (for email/password logins
      // and already-authenticated users with valid cookies)
      // -----------------------------------------------------------
      const token = localStorage.getItem('token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      try {
        const response = await fetch('/api/auth/me', {
          headers,
          credentials: 'include' // Include session cookies
        });
        if (!response.ok) {
          throw new Error('Unauthorized');
        }
        const data = await response.json();
        if (data.user) {
          setUser(data.user);
          setAuthProvider(data.user.auth_provider);

          // Extract GitHub username from user data if available
          if (data.user.github_username) {
            setUserGithubUsername(data.user.github_username);
          }

          // Handle GitHub link redirects - silently handle, don't show alerts
          const linkParams = new URLSearchParams(window.location.search);
          if (linkParams.get('github_linked') === 'true' || linkParams.get('link_error')) {
            window.history.replaceState({}, document.title, window.location.pathname);
          }
        } else {
          throw new Error('No user data');
        }
      } catch (err) {
        console.error('Auth check error:', err);
        // Check for login modal trigger
        const fallbackParams = new URLSearchParams(window.location.search);
        if (fallbackParams.get('open_signin') === 'true') {
          setLoginModalOpen(true);
          window.history.replaceState({}, document.title, window.location.pathname);
        }
      } finally {
        setLoadingUser(false);
      }
    }
    checkAuth();
  }, []);

  // Redirect to landing page if not authenticated
  useEffect(() => {
    if (!loadingUser && !user) {
      window.location.href = '/';
    }
  }, [loadingUser, user]);

  // Fetch conversation list on mount
  useEffect(() => {
    if (loadingUser || !user) return;

    async function fetchConversations() {
      try {
        const response = await fetch('/api/chat/conversations/');
        if (response.ok) {
          const data = await response.json();
          setConversations(data.conversations || []);
        }
      } catch (err) {
        console.error('Failed to load conversations:', err);
      } finally {
        setLoadingConversations(false);
      }
    }
    fetchConversations();
  }, [loadingUser, user]);

  // Load selected conversation detail
  const loadConversation = useCallback(async (convId) => {
    setLoadingMessages(true);
    setMobileSidebarOpen(false);
    setShowSummaryBannerCard(false);
    try {
      const response = await fetch(`/api/chat/conversations/${convId}/`);
      if (response.ok) {
        const data = await response.json();
        setActiveConversation(data.conversation);
        setMessages(data.messages || []);
        setConnectedRepo(data.conversation ? data.conversation.connected_repo : null);
        // Reset explicit repo - if they paste a new link, no PR buttons
        setExplicitRepoId(null);
      }
    } catch (err) {
      console.error('Failed to load conversation details:', err);
    } finally {
      setLoadingMessages(false);
    }
  }, []);

  // Check for conversation query parameter on mount
  useEffect(() => {
    if (loadingUser || !user) return;
    
    const params = new URLSearchParams(window.location.search);
    const conversationId = params.get('conversation');
    if (conversationId) {
      loadConversation(conversationId);
    }
  }, [loadingUser, user, loadConversation]);

  // Sync activeConversation to URL query parameter
  useEffect(() => {
    if (loadingUser || !user) return;

    const params = new URLSearchParams(window.location.search);
    const currentParam = params.get('conversation');
    
    if (activeConversation) {
      if (currentParam !== String(activeConversation.id)) {
        params.set('conversation', activeConversation.id);
        const newUrl = `${window.location.pathname}?${params.toString()}`;
        window.history.pushState({ conversationId: activeConversation.id }, '', newUrl);
      }
    } else {
      if (currentParam) {
        params.delete('conversation');
        const searchStr = params.toString();
        const newUrl = window.location.pathname + (searchStr ? `?${searchStr}` : '');
        window.history.pushState({}, '', newUrl);
      }
    }
  }, [activeConversation, loadingUser, user]);

  // Fetch GitHub repos for dropdown
  useEffect(() => {
    if (connectPopoverOpen && user?.github_is_linked && githubRepos.length === 0) {
      async function fetchGithubRepos() {
        setLoadingGithubRepos(true);
        try {
          const response = await fetch('/api/repos/github/list');
          if (response.ok) {
            const data = await response.json();
            setGithubRepos(data.repos || []);
          }
        } catch (err) {
          console.error('Failed to fetch github repos:', err);
        } finally {
          setLoadingGithubRepos(false);
        }
      }
      fetchGithubRepos();
    }
  }, [connectPopoverOpen, user?.github_is_linked, githubRepos.length]);

  // Auto-grow message input box height
  const handleInputTextareaChange = (e) => {
    setMessageInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  // Initiate New Chat
  const handleNewChat = useCallback(() => {
    setActiveConversation(null);
    setMessages([]);
    setConnectedRepo(null);
    setExplicitRepoId(null);
    setShowSummaryBannerCard(false);
    setMobileSidebarOpen(false);
    setMessageInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, []);

  // Handle browser back/forward buttons (popstate event)
  useEffect(() => {
    const handlePopState = (event) => {
      const params = new URLSearchParams(window.location.search);
      const conversationId = params.get('conversation');
      if (conversationId) {
        loadConversation(conversationId);
      } else {
        handleNewChat();
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [loadConversation, handleNewChat]);

  // Delete Conversation
  const handleDeleteConversation = async (e, convId) => {
    e.stopPropagation();
    setDeleteConversationId(convId);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteConversation = async () => {
    if (!deleteConversationId) return;

    const convId = deleteConversationId;
    setDeleteDialogOpen(false);
    setDeleteConversationId(null);

    if (activeConversation && activeConversation.id === convId) {
      handleNewChat();
    }
    setConversations(prev => prev.filter(c => c.id !== convId));
    try {
      await fetch(`/api/chat/conversations/${convId}/`, { method: 'DELETE' });
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  // Sign out
  const handleSignOut = async (e) => {
    e.preventDefault();
    localStorage.removeItem('token');
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (err) {
      console.error('Sign out error:', err);
    }
    window.location.href = '/';
  };

  // Connect repository mid-chat
  const handleConnectRepo = async (e) => {
    e.preventDefault();
    setConnectError(null);
    setConnectLoading(true);

    let payload = {};
    if (user?.github_is_linked) {
      if (!selectedGithubRepo) {
        setConnectError('Please select a GitHub repository.');
        setConnectLoading(false);
        return;
      }
      payload = {
        repo_url: selectedGithubRepo.repo_url,
        full_name: selectedGithubRepo.full_name,
        default_branch: selectedGithubRepo.default_branch,
        source: 'github_owned'
      };
    } else {
      if (!pastedUrl.trim()) {
        setConnectError('Please paste a public GitHub URL.');
        setConnectLoading(false);
        return;
      }
      payload = { 
        repo_url: pastedUrl.trim(),
        source: 'public_url'
      };
    }

    // Attach active conversation_id to link connected repo
    if (activeConversation) {
      payload.conversation_id = activeConversation.id;
    }

    // Loader delay sequence
    const steps = [
      { text: 'Cloning repo...', delay: 0 },
      { text: 'Analyzing codebase...', delay: 900 },
      { text: 'Generating AI summary...', delay: 1800 }
    ];

    const stepTimers = [];
    steps.forEach(step => {
      const timer = setTimeout(() => {
        setConnectStep(step.text);
      }, step.delay);
      stepTimers.push(timer);
    });

    const startTime = Date.now();

    try {
      const response = await fetch('/api/repos/connect/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to connect repository.');
      }

      // Guarantee progression has run for at least 2 seconds
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 2000 - elapsed);
      await new Promise(resolve => setTimeout(resolve, remaining));

      setConnectedRepo(result.repo);
      setExplicitRepoId(result.repo.id); // Mark as explicitly connected
      setConnectPopoverOpen(false);
      setPastedUrl('');
      setSelectedGithubRepo(null);

      // Refresh sidebar list
      const convResponse = await fetch('/api/chat/conversations/');
      if (convResponse.ok) {
        const data = await convResponse.json();
        setConversations(data.conversations || []);
      }

      // If there is an active conversation, reload it to display system summary message
      if (activeConversation) {
        await loadConversation(activeConversation.id);
      } else {
        // For new chat page, create conversation implicitly & load it
        const initConvRes = await fetch('/api/chat/conversations/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: `Chat: ${result.repo.full_name.split('/').pop()}`,
            repo_id: result.repo.id
          })
        });
        if (initConvRes.ok) {
          const initData = await initConvRes.json();
          await loadConversation(initData.conversation.id);
          // Refresh list again
          const listRes = await fetch('/api/chat/conversations/');
          if (listRes.ok) {
            const listData = await listRes.json();
            setConversations(listData.conversations || []);
          }
        }
      }
    } catch (err) {
      setConnectError(err.message);
    } finally {
      stepTimers.forEach(clearTimeout);
      setConnectLoading(false);
      setConnectStep('');
    }
  };

  // Disconnect Repository (for current chat session)
  const handleDisconnectRepo = async () => {
    setConnectedRepo(null);
    setExplicitRepoId(null);
    setShowSummaryBannerCard(false);

    if (activeConversation) {
      setActiveConversation(prev => prev ? { ...prev, connected_repo: null } : null);
      setConversations(prev => prev.map(c =>
        c.id === activeConversation.id
          ? { ...c, repo_id: null }
          : c
      ));
      try {
        await fetch(`/api/chat/conversations/${activeConversation.id}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ disconnect_repo: true })
        });
      } catch (err) {
        console.error('Failed to disconnect repository on backend:', err);
      }
    }
  };

  // Run Bug Hunt
  const handleBugHunt = async () => {
    if (!connectedRepo || bugHuntLoading) return;
    setBugHuntLoading(true);
    
    // Add loading message
    const loadingMsgId = Date.now();
    setMessages(prev => [...prev, {
      id: loadingMsgId,
      sender: 'assistant',
      text: '🕵️‍♀️ Running Bug Hunt analysis over the entire codebase...',
      is_system_loading: true
    }]);

    try {
      const response = await fetch('/api/ai/bug-hunt/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_id: connectedRepo.id })
      });
      const data = await response.json();
      
      if (!response.ok) throw new Error(data.error || 'Bug hunt failed.');
      
      // Format findings
      let aiText = `### 🐛 Bug Hunter Findings for ${connectedRepo.full_name}\n\n`;
      if (data.findings && data.findings.length > 0) {
        data.findings.forEach(f => {
          aiText += `**${f.file}:${f.line}** [${f.severity}]\n${f.issue}\n\n`;
        });
      } else {
        aiText += "No major vulnerabilities or bugs found! Your code looks clean.";
      }

      // Add actual message and remove loading
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMsgId);
        return [...filtered, {
          id: Date.now() + 1,
          sender: 'assistant',
          text: aiText,
          created_at: new Date().toISOString()
        }];
      });
      
    } catch (err) {
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMsgId);
        return [...filtered, {
          id: Date.now() + 1,
          sender: 'assistant',
          text: `⚠️ **Bug Hunt Error:** ${err.message}`
        }];
      });
    } finally {
      setBugHuntLoading(false);
    }
  };

  // Run Code Review
  const handleCodeReview = async () => {
    if (!connectedRepo || codeReviewLoading) return;
    setCodeReviewLoading(true);

    // Add loading message
    const loadingMsgId = Date.now();
    setMessages(prev => [...prev, {
      id: loadingMsgId,
      sender: 'assistant',
      text: '🔍 Analyzing recent pull requests and changes for code review...',
      is_system_loading: true
    }]);

    try {
      const response = await fetch('/api/ai/code-review/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_id: connectedRepo.id })
      });
      const data = await response.json();

      if (!response.ok) throw new Error(data.error || 'Code review failed.');

      // Add actual message and remove loading
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMsgId);
        return [...filtered, {
          id: Date.now() + 1,
          sender: 'assistant',
          text: data.review,
          created_at: new Date().toISOString()
        }];
      });

    } catch (err) {
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMsgId);
        return [...filtered, {
          id: Date.now() + 1,
          sender: 'assistant',
          text: `⚠️ **Code Review Error:** ${err.message}`
        }];
      });
    } finally {
      setCodeReviewLoading(false);
    }
  };

  // Auto-fix bugs and create PR
  const handleAutoFixWithPR = async () => {
    if (!connectedRepo || autoFixPRLoading) return;
    setAutoFixPRLoading(true);

    // Add loading message
    const loadingMsgId = Date.now();
    setMessages(prev => [...prev, {
      id: loadingMsgId,
      sender: 'assistant',
      text: '🔧 Running bug hunt, generating fixes, and creating pull request...',
      is_system_loading: true
    }]);

    try {
      const response = await fetch('/api/ai/bug-hunt/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_id: connectedRepo.id,
          auto_fix: true,
          create_pr: true
        })
      });
      const data = await response.json();

      if (!response.ok) throw new Error(data.error || 'Auto-fix failed.');

      let aiText = `### 🎉 Auto-Fix PR Created!\n\n`;
      if (data.pr_created) {
        aiText += `**PR Link:** [${data.pr_number} - View on GitHub](${data.pr_url})\n\n`;
      }

      if (data.findings && data.findings.length > 0) {
        aiText += `**Issues Fixed:** ${data.fixes_applied?.length || 0} files updated\n\n`;
        aiText += `**Findings:**\n`;
        data.findings.forEach(f => {
          aiText += `- **${f.file}:${f.line}** [${f.severity}] ${f.issue}\n`;
        });
      } else {
        aiText += "No issues found in your code!";
      }

      // Add actual message and remove loading
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMsgId);
        return [...filtered, {
          id: Date.now() + 1,
          sender: 'assistant',
          text: aiText,
          created_at: new Date().toISOString()
        }];
      });

    } catch (err) {
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== loadingMsgId);
        return [...filtered, {
          id: Date.now() + 1,
          sender: 'assistant',
          text: `⚠️ **Auto-Fix Error:** ${err.message}`
        }];
      });
    } finally {
      setAutoFixPRLoading(false);
    }
  };

  // Repo Editor Functions
  const handleFileClick = async (filePath) => {
    if (!connectedRepo) return;
    
    // remove the root folder name from the path for the github fetch
    const parts = filePath.split('/');
    const relPath = parts.slice(1).join('/');
    
    setEditorFile(relPath);
    setEditorOpen(true);
    setEditorLoading(true);
    setEditorError(null);
    setEditorContent('');
    
    try {
      const response = await fetch(`/api/repos/file?repo_id=${connectedRepo.id}&file_path=${encodeURIComponent(relPath)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to read file.');
      setEditorContent(data.content || '');
    } catch (err) {
      setEditorError(err.message);
    } finally {
      setEditorLoading(false);
    }
  };

  const handleSaveFile = async () => {
    if (!connectedRepo || !editorFile) return;
    setEditorSaving(true);
    setEditorError(null);
    try {
      const response = await fetch('/api/repos/file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_id: connectedRepo.id,
          file_path: editorFile,
          content: editorContent,
          commit_message: `Update ${editorFile} via Project DNA Repo Editor`
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to save file.');

      // Simulate success
      setEditorOpen(false);

      // Add system message
      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'assistant',
        text: `✅ **Committed Successfully!**\n\nYour changes to \`${editorFile}\` have been saved.\nCommit message: *${data.message.split(' (')[0]}*`,
        created_at: new Date().toISOString()
      }]);
    } catch (err) {
      setEditorError(err.message);
    } finally {
      setEditorSaving(false);
    }
  };

  const handleSaveFileWithPR = async () => {
    if (!connectedRepo || !editorFile) return;
    setEditorSaving(true);
    setEditorError(null);
    try {
      const response = await fetch('/api/repos/file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_id: connectedRepo.id,
          file_path: editorFile,
          content: editorContent,
          commit_message: `Update ${editorFile}`,
          create_pr: true,
          pr_title: `Update: ${editorFile}`,
          pr_body: `This pull request updates \`${editorFile}\` with improvements made via Project DNA.\n\nFile: \`${editorFile}\``
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to create PR.');

      setEditorOpen(false);

      let prText = `✅ **Pull Request Created!**\n\n`;
      if (data.pr_created) {
        prText += `**PR #${data.pr_number}** → [View on GitHub](${data.pr_url})\n`;
        prText += `**Branch:** \`${data.branch}\`\n`;
        prText += `**File:** \`${editorFile}\`\n\n`;
        prText += `Your changes have been committed and a pull request has been created for review.`;
      }

      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'assistant',
        text: prText,
        created_at: new Date().toISOString()
      }]);
    } catch (err) {
      setEditorError(err.message);
    } finally {
      setEditorSaving(false);
    }
  };

  // Send message
  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!messageInput.trim() || aiTyping) return;

    const userQuery = messageInput.trim();
    setMessageInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Append user message optimistically to display instantly
    const localUserMsg = {
      id: Date.now(),
      sender: 'user',
      text: userQuery,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, localUserMsg]);
    setAiTyping(true);

    let activeRepoId = connectedRepo ? connectedRepo.id : null;
    let newConnectedRepo = null;

    // GitHub URL auto-detection
    const githubUrlRegex = /https?:\/\/(?:www\.)?github\.com\/[\w.-]+\/[\w.-]+(?:\.git)?\/?(?=\s|$)/i;
    const match = userQuery.match(githubUrlRegex);
    
    if (match && !connectedRepo) {
      let rawUrl = match[0];
      if (rawUrl.endsWith('.git')) rawUrl = rawUrl.slice(0, -4);
      if (rawUrl.endsWith('/')) rawUrl = rawUrl.slice(0, -1);
      
      const payload = { 
        repo_url: rawUrl,
        source: 'public_url'
      };
      if (activeConversation) {
        payload.conversation_id = activeConversation.id;
      }
      
      const loadingMsgId = Date.now() + 1;
      setMessages(prev => [...prev, {
        id: loadingMsgId,
        sender: 'assistant',
        text: '⏳ Connecting to GitHub repo...',
        is_system_loading: true
      }]);
      
      try {
        const response = await fetch('/api/repos/connect/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        
        let result = {};
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          result = await response.json();
        } else {
          const textRes = await response.text();
          if (!response.ok) {
            throw new Error(`Server error (${response.status}): ${textRes.substring(0, 100) || 'Empty response'}`);
          }
        }
        
        if (!response.ok) {
          throw new Error(result.error || 'Failed to connect repository.');
        }
        
        newConnectedRepo = result.repo;
        activeRepoId = newConnectedRepo.id;
        setConnectedRepo(newConnectedRepo);
        
        // Remove loading message on success
        setMessages(prev => prev.filter(m => m.id !== loadingMsgId));
        
      } catch (err) {
        // Replace loading message with error
        setMessages(prev => prev.map(m => m.id === loadingMsgId ? {
          ...m,
          text: `⚠️ **Couldn't access that repository** — it may be private or the link may be incorrect.`,
          is_system_loading: false
        } : m));
      }
    }

    try {
      const payload = {
        message: userQuery,
        conversation_id: activeConversation ? activeConversation.id : null,
        repo_id: activeRepoId
      };

      const response = await fetch('/api/chat/send/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      let data = {};
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const textResponse = await response.text();
        if (!response.ok) {
          throw new Error(`Server error (${response.status}): ${textResponse.substring(0, 100) || 'Empty response'}`);
        }
      }

      if (!response.ok) {
        throw new Error(data.error || 'Failed to send message.');
      }

      // Add AI response to conversation logs
      setMessages(prev => [...prev, data.ai_message]);

      // Auto-detect PR creation requests is handled manually via button click. No auto-actions taken.

      // If we created a new conversation implicitly, select it and reload history
      if (!activeConversation) {
        setActiveConversation({
          id: data.conversation_id,
          title: data.conversation_title,
          connected_repo: newConnectedRepo || connectedRepo,
          updated_at: new Date().toISOString()
        });

        // Fetch new list
        const listRes = await fetch('/api/chat/conversations/');
        if (listRes.ok) {
          const listData = await listRes.json();
          setConversations(listData.conversations || []);
        }
      } else {
        // Simply update local history modified timestamp
        setConversations(prev => prev.map(c =>
          c.id === activeConversation.id
            ? { ...c, updated_at: new Date().toISOString(), title: data.conversation_title }
            : c
        ));
      }
    } catch (err) {
      console.error(err);
      // Append a warning error message system fallback
      setMessages(prev => [...prev, {
        id: Date.now() + 2,
        sender: 'assistant',
        text: `⚠️ **Error:** ${err.message}. Please click retry or type your message again.`
      }]);
    } finally {
      setAiTyping(false);
    }
  };

  // Group conversations by date labels (with proper timezone handling)
  const groupConversations = (list) => {
    // Copy the list to prevent in-place state mutation issues in React
    return [...list].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
  };

  const conversationsGrouped = groupConversations(conversations);

  // Format name initials
  const getInitials = () => {
    if (!user || !user.name) return 'U';
    return user.name.split(' ').map(n => n[0]).join('').slice(0,2).toUpperCase();
  };

  // Toggle tree nodes
  const handleToggleNode = (path) => {
    setCollapsedNodes(prev => ({ ...prev, [path]: !prev[path] }));
  };

  const filteredDropdownRepos = githubRepos.filter(r => 
    r.full_name.toLowerCase().includes(githubSearch.toLowerCase())
  );

  return (
    <>
      <LoginModal
        isOpen={loginModalOpen}
        onClose={() => setLoginModalOpen(false)}
        onLoginSuccess={() => {
          setLoginModalOpen(false);
          window.location.reload();
        }}
      />

      <ConfirmDialog
        isOpen={deleteDialogOpen}
        title="Delete chat?"
        message="Are you sure you want to delete this chat? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        isDangerous={true}
        onConfirm={confirmDeleteConversation}
        onCancel={() => setDeleteDialogOpen(false)}
      />

      <ConfirmDialog
        isOpen={prConfirmDialogOpen}
        title="Create pull request?"
        message="Review the suggested code changes above. Proceed with creating a PR?"
        confirmText="Create PR"
        cancelText="Cancel"
        onConfirm={() => {
          setPrConfirmDialogOpen(false);
          handleAutoFixWithPR();
        }}
        onCancel={() => setPrConfirmDialogOpen(false)}
      />

      {/* 5. APPLY FIX DIALOG */}
      {applyFixDialogOpen && (
        <div className="modal-overlay open" style={{ zIndex: 400, display: 'flex' }}>
          <div className="modal-card confirm-dialog" style={{ maxWidth: '500px', padding: '24px' }}>
            <div className="confirm-dialog-header" style={{ marginBottom: '16px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text)' }}>Apply Fix & Open PR</h2>
            </div>
            <div className="confirm-dialog-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div className="modal-form-group">
                <label style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-muted)' }}>Target File Path</label>
                <input
                  type="text"
                  className="text-input"
                  value={applyFixFilePath}
                  onChange={(e) => setApplyFixFilePath(e.target.value)}
                  style={{ width: '100%', marginTop: '4px', padding: '8px 10px', fontSize: '13px', background: 'var(--bg)', color: 'var(--text)', border: '1px solid var(--border)' }}
                  placeholder="e.g. src/App.css"
                  required
                />
              </div>
              <div className="modal-form-group">
                <label style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-muted)' }}>Fix Description</label>
                <textarea
                  className="text-input"
                  value={applyFixDescription}
                  onChange={(e) => setApplyFixDescription(e.target.value)}
                  style={{ width: '100%', marginTop: '4px', padding: '8px 10px', fontSize: '13px', minHeight: '80px', fontFamily: 'inherit', resize: 'vertical', background: 'var(--bg)', color: 'var(--text)', border: '1px solid var(--border)' }}
                  placeholder="Describe what the fix does (sent to LLM code generator)"
                  required
                />
              </div>
            </div>
            <div className="confirm-dialog-footer" style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button onClick={() => setApplyFixDialogOpen(false)} className="confirm-btn-cancel" style={{ padding: '8px 16px', background: 'var(--bg-alt)', border: '1px solid var(--border)', borderRadius: '4px', cursor: 'pointer' }}>
                Cancel
              </button>
              <button
                onClick={() => handleApplyFixAndOpenPR(applyFixFilePath, applyFixDescription)}
                disabled={!applyFixFilePath.trim() || !applyFixDescription.trim()}
                className="btn-emerald"
                style={{ padding: '8px 16px', border: 'none', borderRadius: '4px', cursor: 'pointer', opacity: (!applyFixFilePath.trim() || !applyFixDescription.trim()) ? 0.6 : 1 }}
              >
                Apply and PR
              </button>
            </div>
          </div>
        </div>
      )}

      {!user && loadingUser ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
          <svg className="spinner" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
        </div>
      ) : !user ? (
        <LandingPage onSignIn={() => setLoginModalOpen(true)} />
      ) : (
        <div className="dashboard-container">
      {/* Sidebar mobile overlay trigger */}
      {mobileSidebarOpen && (
        <div className="sidebar-overlay mobile-open" onClick={() => setMobileSidebarOpen(false)}></div>
      )}

      {/* 1. SIDEBAR PANEL */}
      <aside className={`sidebar ${mobileSidebarOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-header">
          <div className="logo-container">
            <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '24px', height: '24px' }}>
              <path d="M8 4C8 4 12 8 14 14C16 20 20 24 20 24" stroke="#1A1A1A" strokeWidth="2.2" strokeLinecap="round"/>
              <path d="M20 4C20 4 16 8 14 14C12 20 8 24 8 24" stroke="#2D6A4F" strokeWidth="2.2" strokeLinecap="round"/>
              <line x1="9" y1="9" x2="19" y2="9" stroke="#E5E5E2" strokeWidth="1.5" strokeLinecap="round"/>
              <line x1="8" y1="14" x2="20" y2="14" stroke="#E5E5E2" strokeWidth="1.5" strokeLinecap="round"/>
              <line x1="9" y1="19" x2="19" y2="19" stroke="#E5E5E2" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <span>Project DNA</span>
          </div>
          <button className="btn-new-chat" onClick={handleNewChat}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5v14"/></svg>
            New chat
          </button>
        </div>

        {/* past chats list */}
        <div className="sidebar-conversations">
          {loadingConversations ? (
            /* skeleton loader list */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '12px' }}>
              <div style={{ height: '24px', background: 'var(--bg-alt)', borderRadius: '4px', width: '80%' }}></div>
              <div style={{ height: '24px', background: 'var(--bg-alt)', borderRadius: '4px', width: '90%' }}></div>
              <div style={{ height: '24px', background: 'var(--bg-alt)', borderRadius: '4px', width: '70%' }}></div>
            </div>
          ) : conversations.length === 0 ? (
            <div style={{ padding: '24px 12px', textAlign: 'center', fontSize: '12px', color: 'var(--text-faint)' }}>
              No conversations yet
            </div>
          ) : (
            conversationsGrouped.map(c => (
              <button
                key={c.id}
                className={`chat-history-item ${activeConversation?.id === c.id ? 'active' : ''}`}
                onClick={() => loadConversation(c.id)}
              >
                <span className="chat-history-title">{c.title}</span>
                <span className="chat-history-delete-btn" onClick={(e) => handleDeleteConversation(e, c.id)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                </span>
              </button>
            ))
          )}
        </div>

        {/* Sidebar account footer */}
        {user && (
          <div className="sidebar-footer">
            <div className="user-profile">
              <div className="user-avatar">{getInitials()}</div>
              <div className="user-info">
                <span className="user-name" title={user.name}>
                  {user.name}
                  {user.github_is_linked && (
                    <svg title="GitHub Connected" viewBox="0 0 24 24" fill="currentColor" style={{ width: '12px', height: '12px', marginLeft: '6px', color: 'var(--text-faint)' }}><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-3.96-1.385-.09-.225-.48-1.385-1.02-1.755-.42-.27-1.02-.81-.015-.825.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                  )}
                </span>
                <span className="user-email" title={user.email}>{user.email}</span>
              </div>
            </div>
            <div className="sidebar-footer-links">
              <a href="#" className="sidebar-link" onClick={(e) => { e.preventDefault(); handleSignOut(e); }}>Sign out</a>
            </div>
          </div>
        )}
      </aside>

      {/* 2. MAIN CHAT PANEL / DASHBOARD */}
      <main className="main-content main-chat-panel">

        {/* Mobile menu responsive toggle header */}
            <div className="mobile-header">
          <button className="mobile-hamburger" onClick={() => setMobileSidebarOpen(true)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>
          </button>
          <span style={{ fontSize: '14px', fontWeight: 600 }}>Project DNA</span>
          <button className="mobile-hamburger" onClick={handleNewChat}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5v14"/></svg>
          </button>
        </div>

        {/* Sticky top banner when repository connected */}
        {connectedRepo && (
          <div className="repo-summary-banner">
            <div className="repo-summary-banner-header">
              <div className="repo-banner-info">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/></svg>
                <span>📁 {connectedRepo.full_name}</span>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button className="btn-view-summary" onClick={() => setShowSummaryBannerCard(!showSummaryBannerCard)}>
                  <span>{showSummaryBannerCard ? 'Hide analysis' : 'View summary'}</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ transform: showSummaryBannerCard ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }}><path d="m6 9 6 6 6-6"/></svg>
                </button>
              </div>
            </div>

            {showSummaryBannerCard && (
              <div className="repo-summary-card">
                {/* Left Card content: Codebase summary */}
                <div className="repo-summary-card-col60">
                  <span className="repo-summary-card-title">Codebase Summary</span>
                  <div className="tech-stack-pills" style={{ marginTop: '4px', marginBottom: '8px' }}>
                    {connectedRepo.tech_stack?.map((tech, idx) => (
                      <span key={idx} className="tech-pill">{tech}</span>
                    ))}
                  </div>
                  <div style={{ fontSize: '13px', lineHeight: 1.5, color: 'var(--text)' }}>
                    {connectedRepo.ai_summary?.split('\n\n').map((para, idx) => {
                      if (para.startsWith('### ')) {
                        return <h4 key={idx} style={{ fontWeight: 600, marginTop: '8px', marginBottom: '4px' }}>{para.replace('### ', '')}</h4>;
                      }
                      return <p key={idx} style={{ marginBottom: '8px' }}>{para}</p>;
                    })}
                  </div>
                </div>

                {/* Right Card content: File Tree */}
                <div className="repo-summary-card-col40">
                  <span className="repo-summary-card-title">
                    File Tree ({connectedRepo.file_count} files)
                  </span>
                  <div style={{ overflowX: 'auto', marginTop: '6px' }}>
                    {connectedRepo.file_tree ? (
                      <FileTreeNode 
                        node={connectedRepo.file_tree}
                        path={connectedRepo.file_tree.name}
                        collapsedNodes={collapsedNodes}
                        onToggle={handleToggleNode}
                        onFileClick={handleFileClick}
                      />
                    ) : (
                      <span style={{ fontSize: '12px', color: 'var(--text-faint)' }}>No file tree</span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Editor Modal Overlay */}
        {editorOpen && (
          <div className="modal-overlay open" style={{ zIndex: 300, display: 'flex' }}>
            <div className="modal-card" style={{ maxWidth: '800px', height: '80vh', display: 'flex', flexDirection: 'column', padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 600 }}>📝 Editing: {editorFile}</h3>
                <button onClick={() => setEditorOpen(false)} style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', color: 'var(--text-muted)' }}>&times;</button>
              </div>
              
              {editorError && (
                <div style={{ background: '#FFEBEE', color: '#D32F2F', padding: '12px', borderRadius: '4px', marginBottom: '16px', fontSize: '13px' }}>
                  {editorError}
                </div>
              )}
              
              <div style={{ flex: 1, position: 'relative', border: '1px solid var(--border)', borderRadius: '4px', overflow: 'hidden' }}>
                {editorLoading ? (
                  <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                    <svg className="spinner" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
                  </div>
                ) : (
                  <textarea 
                    value={editorContent}
                    onChange={(e) => setEditorContent(e.target.value)}
                    style={{ 
                      width: '100%', 
                      height: '100%', 
                      padding: '16px', 
                      fontFamily: 'monospace', 
                      fontSize: '13px', 
                      lineHeight: '1.5',
                      border: 'none',
                      outline: 'none',
                      resize: 'none',
                      background: '#1E1E1E',
                      color: '#D4D4D4'
                    }}
                  />
                )}
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '16px' }}>
                <button onClick={() => setEditorOpen(false)} style={{ padding: '8px 16px', background: 'var(--bg-alt)', border: '1px solid var(--border)', borderRadius: '4px', fontWeight: 500 }}>Cancel</button>
                {canPerformWriteActions && (
                  <>
                    <button
                      onClick={handleSaveFile}
                      disabled={editorLoading || editorSaving}
                      style={{ padding: '8px 16px', background: 'var(--accent)', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 500 }}
                    >
                      {editorSaving ? 'Committing...' : 'Commit Changes'}
                    </button>
                    <button
                      onClick={handleSaveFileWithPR}
                      disabled={editorLoading || editorSaving}
                      style={{ padding: '8px 16px', background: '#2D6A4F', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 500 }}
                    >
                      {editorSaving ? 'Creating PR...' : 'Create PR'}
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Scrollable messages container / viewport */}
        {loadingMessages ? (
          <div style={{ display: 'flex', flexGrow: 1, alignItems: 'center', justifyContent: 'center' }}>
            <svg className="spinner" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
          </div>
        ) : messages.length === 0 ? (
          /* EMPTY CHAT SCREEN */
          <div className="empty-state">
            <div className="empty-mark">
              <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '48px', height: '48px' }}>
                <path d="M8 4C8 4 12 8 14 14C16 20 20 24 20 24" stroke="#1A1A1A" strokeWidth="2.2" strokeLinecap="round"/>
                <path d="M20 4C20 4 16 8 14 14C12 20 8 24 8 24" stroke="#2D6A4F" strokeWidth="2.2" strokeLinecap="round"/>
                <line x1="9" y1="9" x2="19" y2="9" stroke="#E5E5E2" strokeWidth="1.5" strokeLinecap="round"/>
                <line x1="8" y1="14" x2="20" y2="14" stroke="#E5E5E2" strokeWidth="1.5" strokeLinecap="round"/>
                <line x1="9" y1="19" x2="19" y2="19" stroke="#E5E5E2" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <h1 className="empty-title">What do you want to understand today?</h1>
          </div>
        ) : (
          /* CONVERSATION VIEWER */
          <div className="chat-messages-container">
            {messages.map((msg) => {
              const isUser = msg.sender === 'user';
              const isSystemAcknowledgment = !isUser && msg.text.startsWith("I've successfully connected to");
              
              return (
                <div key={msg.id} className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}>
                  {!isUser && (
                    <div className="message-avatar">
                      <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '18px', height: '18px' }}>
                        <path d="M8 4C8 4 12 8 14 14C16 20 20 24 20 24" stroke="#1A1A1A" strokeWidth="2.2" strokeLinecap="round"/>
                        <path d="M20 4C20 4 16 8 14 14C12 20 8 24 8 24" stroke="#2D6A4F" strokeWidth="2.2" strokeLinecap="round"/>
                        <line x1="9" y1="9" x2="19" y2="9" stroke="#E5E5E2" strokeWidth="1.5" strokeLinecap="round"/>
                        <line x1="8" y1="14" x2="20" y2="14" stroke="#E5E5E2" strokeWidth="1.5" strokeLinecap="round"/>
                        <line x1="9" y1="19" x2="19" y2="19" stroke="#E5E5E2" strokeWidth="1.5" strokeLinecap="round"/>
                      </svg>
                    </div>
                  )}
                  
                  <div className={`message-content ${isSystemAcknowledgment ? 'system-msg' : ''}`}>
                    <MarkdownRenderer content={msg.text} />

                    {/* Show PR and Review buttons ONLY on follow-up AI messages (not initial summary) */}
                    {!isUser && connectedRepo && canPerformWriteActions && !msg.text.includes('I\'ve successfully connected to') && !msg.text.includes('PR created') && !msg.text.includes('PR Link') && !msg.text.includes('Opened pull request') && (() => {
                      const parsedPath = extractFilePath(msg.text);
                      return (
                        <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                            <button
                              onClick={() => {
                                setApplyFixFilePath(parsedPath || '');
                                setApplyFixDescription(msg.text.substring(0, 500));
                                setApplyFixDialogOpen(true);
                              }}
                              disabled={applyFixLoading}
                              style={{
                                padding: '8px 16px',
                                background: 'var(--accent)',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                fontWeight: 500,
                                fontSize: '13px',
                                cursor: 'pointer',
                                opacity: applyFixLoading ? 0.6 : 1
                              }}
                            >
                              {applyFixLoading ? 'Creating PR...' : 'Create PR'}
                            </button>
                            <button
                              onClick={() => {
                                setReviewingMsgId(msg.id);
                                setReviewPrNumber('');
                              }}
                              style={{
                                padding: '8px 16px',
                                background: 'transparent',
                                color: 'var(--accent)',
                                border: '1px solid var(--accent)',
                                borderRadius: '6px',
                                fontWeight: 500,
                                fontSize: '13px',
                                cursor: 'pointer'
                              }}
                            >
                              Review PR
                            </button>
                          </div>

                          {reviewingMsgId === msg.id && (
                            <div style={{ marginTop: '8px', display: 'flex', gap: '8px', alignItems: 'center' }}>
                              <input
                                type="text"
                                placeholder="Enter PR Number..."
                                value={reviewPrNumber}
                                onChange={(e) => setReviewPrNumber(e.target.value.replace(/\D/g, ''))}
                                style={{
                                  padding: '6px 10px',
                                  border: '1px solid var(--border)',
                                  borderRadius: '6px',
                                  fontSize: '13px',
                                  width: '140px',
                                  outline: 'none',
                                  background: 'var(--bg)',
                                  color: 'var(--text)'
                                }}
                              />
                              <button
                                onClick={() => handleReviewPRSubmit(reviewPrNumber)}
                                disabled={!reviewPrNumber.trim() || reviewPrLoading}
                                style={{
                                  padding: '6px 12px',
                                  background: 'var(--accent)',
                                  color: 'white',
                                  border: 'none',
                                  borderRadius: '6px',
                                  fontWeight: 500,
                                  fontSize: '13px',
                                  cursor: 'pointer',
                                  opacity: (!reviewPrNumber.trim() || reviewPrLoading) ? 0.6 : 1
                                }}
                              >
                                {reviewPrLoading ? 'Reviewing...' : 'Submit'}
                              </button>
                              <button
                                onClick={() => setReviewingMsgId(null)}
                                style={{
                                  padding: '6px 12px',
                                  background: 'transparent',
                                  color: 'var(--text-muted)',
                                  border: '1px solid var(--border)',
                                  borderRadius: '6px',
                                  fontWeight: 500,
                                  fontSize: '13px',
                                  cursor: 'pointer'
                                }}
                              >
                                Cancel
                              </button>
                            </div>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                </div>
              );
            })}

            {/* Simulated typing dot animation */}
            {aiTyping && (
              <div className="message-wrapper assistant">
                <div className="message-avatar">
                  <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ width: '18px', height: '18px' }}>
                    <path d="M8 4C8 4 12 8 14 14C16 20 20 24 20 24" stroke="#1A1A1A" strokeWidth="2.2" strokeLinecap="round"/>
                    <path d="M20 4C20 4 16 8 14 14C12 20 8 24 8 24" stroke="#2D6A4F" strokeWidth="2.2" strokeLinecap="round"/>
                    <line x1="9" y1="9" x2="19" y2="9" stroke="#E5E5E2" strokeWidth="1.5" strokeLinecap="round"/>
                    <line x1="8" y1="14" x2="20" y2="14" stroke="#E5E5E2" strokeWidth="1.5" strokeLinecap="round"/>
                    <line x1="9" y1="19" x2="19" y2="19" stroke="#E5E5E2" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                </div>
                <div className="typing-indicator">
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* 3. BOTTOM CHAT INPUT WRAPPER */}
        <div className="chat-input-wrapper">

          {/* Disclaimer */}
          <div style={{ textAlign: 'center', fontSize: '11px', color: 'var(--text-faint)', marginBottom: '12px', padding: '0 16px' }}>
            Project DNA can make mistakes. Please review all code changes before merging to your repository.
          </div>
          
          {/* Connector Pill / Connected chip */}
          <div className="repo-connector-pill-container" ref={popoverRef}>
            {connectedRepo ? (
              <div className="repo-connected-chip">
                <span>📁 {connectedRepo.full_name}</span>
                <button className="btn-disconnect-chip" onClick={handleDisconnectRepo}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
                </button>
              </div>
            ) : (
              <button className="btn-connect-pill" onClick={() => setConnectPopoverOpen(!connectPopoverOpen)}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m18 8 4 4-4 4M6 16l-4-4 4-4M2 12h20"/></svg>
                Connect a repo
              </button>
            )}

            {/* Lightweight popover connection control */}
            {connectPopoverOpen && (
              <div className="repo-popover">
                <div className="popover-header">Connect a codebase</div>
                
                {connectLoading ? (
                  /* popover loading states */
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '12px 0' }}>
                    <svg className="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
                    <span style={{ fontSize: '12px', fontWeight: 500 }}>{connectStep}</span>
                  </div>
                ) : (
                  <form onSubmit={handleConnectRepo} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {connectError && (
                      <div className="error-banner" style={{ fontSize: '11px', padding: '6px' }}>
                        <span>{connectError}</span>
                      </div>
                    )}
                    
                    {user?.github_is_linked ? (
                      /* searchable github dropdown inside popover */
                      <div className="modal-form-group">
                        <button 
                          type="button" 
                          className="dropdown-trigger"
                          style={{ padding: '8px 10px', fontSize: '13px' }}
                          onClick={() => setGithubDropdownOpen(!githubDropdownOpen)}
                        >
                          <span>{selectedGithubRepo ? selectedGithubRepo.full_name : 'Select repository...'}</span>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
                        </button>

                        {githubDropdownOpen && (
                          <div className="dropdown-menu" style={{ top: '100%', width: '100%', maxHeight: '150px' }}>
                            <div className="dropdown-search-container" style={{ padding: '4px' }}>
                              <input 
                                type="text" 
                                className="dropdown-search-input" 
                                placeholder="Search repos..."
                                value={githubSearch}
                                onChange={(e) => setGithubSearch(e.target.value)}
                                onClick={(e) => e.stopPropagation()}
                              />
                            </div>
                            {loadingGithubRepos ? (
                              <div style={{ padding: '8px', textAlign: 'center' }}>
                                <svg className="spinner" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
                              </div>
                            ) : filteredDropdownRepos.length === 0 ? (
                              <div style={{ padding: '8px', fontSize: '12px', color: 'var(--text-faint)', textAlign: 'center' }}>
                                No repos found
                              </div>
                            ) : (
                              filteredDropdownRepos.map((repo, idx) => (
                                <div 
                                  key={idx}
                                  className="dropdown-item"
                                  style={{ padding: '6px 8px' }}
                                  onClick={() => {
                                    setSelectedGithubRepo(repo);
                                    setGithubDropdownOpen(false);
                                  }}
                                >
                                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                                    <span style={{ fontWeight: 500, fontSize: '12px' }}>{repo.name}</span>
                                    {repo.language && <span style={{ fontSize: '10px', color: 'var(--text-faint)' }}>{repo.language}</span>}
                                  </div>
                                </div>
                              ))
                            )}
                          </div>
                        )}
                        <button type="submit" className="btn-emerald" disabled={!selectedGithubRepo} style={{ padding: '8px', fontSize: '12px', marginTop: '10px', width: '100%' }}>
                          Connect
                        </button>
                      </div>
                    ) : (
                      /* paste input field inside popover */
                      <>
                        <div className="modal-form-group">
                          <input 
                            type="url" 
                            className="text-input"
                            style={{ padding: '8px 10px', fontSize: '13px' }}
                            placeholder="Paste a public GitHub repo URL"
                            value={pastedUrl}
                            onChange={(e) => setPastedUrl(e.target.value)}
                            required
                          />
                        </div>
                        <button type="submit" className="btn-emerald" disabled={!/^https?:\/\/(?:www\.)?github\.com\/[\w.-]+\/[\w.-]+(?:\.git)?\/?$/.test(pastedUrl.trim())} style={{ padding: '8px', fontSize: '12px', width: '100%' }}>
                          Connect
                        </button>

                        <div className="popover-divider">
                          <span>or</span>
                        </div>

                        <button 
                          type="button" 
                          className="btn-secondary-full" 
                          onClick={() => {
                            const apiBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
                            window.location.href = `${apiBaseUrl}/api/auth/github/link/?token=${localStorage.getItem('token')}`;
                          }}
                        >
                          <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: '14px', height: '14px' }}><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-3.96-1.385-.09-.225-.48-1.385-1.02-1.755-.42-.27-1.02-.81-.015-.825.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                          Connect GitHub for full access
                        </button>
                        <p style={{ fontSize: '10px', color: 'var(--text-faint)', textAlign: 'center', marginTop: '6px', lineHeight: 1.3 }}>
                          Unlocks your repo list, code editing, and pull requests.
                        </p>
                      </>
                    )}
                  </form>
                )}
              </div>
            )}
          </div>

          {/* Text input area and send trigger */}
          <form onSubmit={handleSendMessage}>
            <div className="chat-input-box">
              <textarea 
                ref={textareaRef}
                className="chat-textarea"
                rows="1"
                placeholder={
                  connectedRepo 
                    ? `Ask about ${connectedRepo.full_name.split('/').pop()} — find bugs, request a fix, or ask how something works` 
                    : "Ask anything about your code, paste a snippet, or describe a bug"
                }
                value={messageInput}
                onChange={handleInputTextareaChange}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
              />
              <div className="chat-input-footer">
                <button type="submit" className="btn-send" disabled={!messageInput.trim() || aiTyping}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="12" y1="19" x2="12" y2="5"></line>
                    <polyline points="5 12 12 5 19 12"></polyline>
                  </svg>
                </button>
              </div>
            </div>
          </form>

        </div>
      </main>
    </div>
    )}
    </>
    );
  }

export default App;
