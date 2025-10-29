document.addEventListener('DOMContentLoaded', () => {
  const videoInput = document.getElementById('videoId');
  const appUrlInput = document.getElementById('appUrl');
  const openBtn = document.getElementById('openBtn');
  const copyBtn = document.getElementById('copyBtn');

  // Try to ask the active tab for the video id first
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    if (!tab) return;
    chrome.tabs.sendMessage(tab.id, 'GET_VIDEO_ID', (resp) => {
      if (resp && resp.videoId) {
        videoInput.value = resp.videoId;
      } else {
        // fallback to storage
        chrome.storage.local.get(['yt_video_id'], (items) => {
          if (items && items.yt_video_id) videoInput.value = items.yt_video_id;
        });
      }
    });
  });

  function buildUrl() {
    const vid = (videoInput.value || '').trim();
    const base = (appUrlInput.value || '').trim() || 'http://localhost:8501';
    if (!vid) return base;
    // append video_id as query param and request auto-indexing
    const sep = base.includes('?') ? '&' : '?';
    return `${base}${sep}video_id=${encodeURIComponent(vid)}&auto_index=true`;
  }

  openBtn.addEventListener('click', () => {
    const url = buildUrl();
    chrome.tabs.create({ url });
  });

  copyBtn.addEventListener('click', () => {
    const url = buildUrl();
    navigator.clipboard.writeText(url).then(() => {
      copyBtn.textContent = 'Copied';
      setTimeout(() => (copyBtn.textContent = 'Copy URL'), 1200);
    });
  });
});
