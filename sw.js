// Service Worker for HSK Audio Player
// オフライン音声キャッシュ機能をサポート

const CACHE_NAME = 'hsk-audio-cache-v1';
const STATIC_CACHE_NAME = 'hsk-static-v1';

// 静的リソース
const STATIC_RESOURCES = [
  '/',
  '/audio_player_mobile_enhanced.html'
];

// インストール時の処理
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then(cache => {
        console.log('Caching static resources...');
        return cache.addAll(STATIC_RESOURCES);
      })
      .then(() => {
        console.log('Service Worker installed successfully');
        return self.skipWaiting();
      })
  );
});

// アクティベート時の処理
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          // 古いキャッシュを削除
          if (cacheName !== CACHE_NAME && cacheName !== STATIC_CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Service Worker activated successfully');
      return self.clients.claim();
    })
  );
});

// フェッチリクエストの処理
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // 音声ファイルの場合
  if (url.pathname.includes('/Sound_level_') && url.pathname.endsWith('.mp3')) {
    event.respondWith(
      caches.open(CACHE_NAME)
        .then(cache => {
          return cache.match(request)
            .then(cachedResponse => {
              if (cachedResponse) {
                console.log('Serving audio from cache:', url.pathname);
                return cachedResponse;
              }
              
              // キャッシュにない場合はネットワークから取得
              return fetch(request)
                .then(networkResponse => {
                  if (networkResponse.ok) {
                    // レスポンスをキャッシュに保存
                    cache.put(request, networkResponse.clone());
                  }
                  return networkResponse;
                })
                .catch(error => {
                  console.error('Network fetch failed for audio:', url.pathname, error);
                  throw error;
                });
            });
        })
    );
  }
  // HTMLファイルの場合
  else if (request.destination === 'document') {
    event.respondWith(
      caches.open(STATIC_CACHE_NAME)
        .then(cache => {
          return cache.match(request)
            .then(cachedResponse => {
              return cachedResponse || fetch(request);
            });
        })
    );
  }
  // その他のリクエストはそのまま通す
  else {
    event.respondWith(fetch(request));
  }
});

// メッセージ処理（アプリからの指示）
self.addEventListener('message', event => {
  const { action, data } = event.data;
  
  switch (action) {
    case 'CACHE_AUDIO_FILES':
      event.waitUntil(cacheAudioFiles(data.audioFiles));
      break;
      
    case 'CLEAR_AUDIO_CACHE':
      event.waitUntil(clearAudioCache());
      break;
      
    case 'GET_CACHE_INFO':
      event.waitUntil(getCacheInfo().then(info => {
        event.ports[0].postMessage(info);
      }));
      break;
  }
});

// 音声ファイルのキャッシュ
async function cacheAudioFiles(audioFiles) {
  try {
    const cache = await caches.open(CACHE_NAME);
    
    for (const audioFile of audioFiles) {
      try {
        const response = await fetch(audioFile);
        if (response.ok) {
          await cache.put(audioFile, response);
          console.log('Cached audio file:', audioFile);
        }
      } catch (error) {
        console.warn('Failed to cache audio file:', audioFile, error);
      }
    }
    
    console.log('Audio caching completed');
  } catch (error) {
    console.error('Audio caching failed:', error);
  }
}

// 音声キャッシュのクリア
async function clearAudioCache() {
  try {
    await caches.delete(CACHE_NAME);
    console.log('Audio cache cleared');
  } catch (error) {
    console.error('Failed to clear audio cache:', error);
  }
}

// キャッシュ情報の取得
async function getCacheInfo() {
  try {
    const cache = await caches.open(CACHE_NAME);
    const keys = await cache.keys();
    
    return {
      audioFilesCount: keys.length,
      cacheNames: await caches.keys()
    };
  } catch (error) {
    console.error('Failed to get cache info:', error);
    return {
      audioFilesCount: 0,
      cacheNames: []
    };
  }
} 