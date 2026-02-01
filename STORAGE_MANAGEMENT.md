# Storage Management Feature

## Overview

Added storage monitoring and cleanup features to help users manage ChromaDB storage space and remove old indexed repositories.

---

## Features

### 1. **Storage Usage Display**

Located at the bottom of the sidebar, shows:
- Current storage used vs. maximum (1GB limit)
- Usage percentage
- Visual progress bar
- Color-coded status indicator

**Display Format:**
```
💾 Storage
✅ 542MB / 1024MB (53%)
[████████░░░░░░░░░░░░] 53%
```

**Color Coding:**
- 🟢 **Green** (<70%): `✅ Storage healthy`
- 🟡 **Yellow** (70-90%): `⚠️ Storage getting full`
- 🔴 **Red** (>90%): `🔴 Storage nearly full`

### 2. **Capacity Warnings**

**At 80% Usage:**
```
⚠️ Storage at 80%. Consider removing old repos.
```

**At 95% Usage:**
```
🔴 Storage nearly full! Remove repos before indexing new ones.
```
- Disables "Index Repository" button
- Prevents new repository indexing
- Shows error message in GitHub indexing section

### 3. **Cleanup Button**

**Button Text:** `🗑️ Clear My Repos (X repos)`
- Only appears if user has indexed repositories
- Shows count of user repositories
- Located below storage meter

**Confirmation Dialog:**
```
⚠️ This will delete X repositories. Are you sure?

[✅ Yes, Delete]  [❌ Cancel]
```

### 4. **Cleanup Process**

When user confirms deletion:
1. Deletes all collections matching `session_{session_id}_*`
2. Clears `st.session_state['user_repos']`
3. Updates storage metrics
4. Switches to default repo if current was deleted
5. Shows success message with freed space

**Success Message:**
```
✅ Deleted 3 repos. Freed 245MB.
```

---

## Technical Implementation

### Helper Functions

#### `get_storage_size()`
```python
def get_storage_size() -> float:
    """Calculate total size of chroma_db directory in MB"""
    total = 0
    for dirpath, dirnames, filenames in os.walk('./chroma_db'):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)  # Convert to MB
```

#### `get_storage_percent()`
```python
def get_storage_percent(max_storage_mb: float = 1024) -> float:
    """Calculate storage usage percentage"""
    current_size = get_storage_size()
    return (current_size / max_storage_mb) * 100
```

#### `format_size()`
```python
def format_size(size_mb: float) -> str:
    """Format size in human-readable format"""
    if size_mb >= 1024:
        return f"{size_mb / 1024:.1f}GB"
    else:
        return f"{size_mb:.0f}MB"
```

#### `delete_user_collections()`
```python
def delete_user_collections(session_id: str) -> dict:
    """Delete all collections for current session"""
    client = chromadb.PersistentClient(path="./chroma_db")
    collections = client.list_collections()
    
    deleted_count = 0
    size_before = get_storage_size()
    
    for col in collections:
        if col.name.startswith(f"session_{session_id}_"):
            client.delete_collection(col.name)
            deleted_count += 1
    
    size_after = get_storage_size()
    size_freed = size_before - size_after
    
    return {
        "status": "success",
        "count": deleted_count,
        "size_freed": size_freed
    }
```

### Storage Caching

To avoid constant recalculation:

```python
# Session state
st.session_state.storage_size = 0.0
st.session_state.storage_last_updated = 0

# Update every 30 seconds
current_time = time.time()
if current_time - st.session_state.storage_last_updated > 30:
    st.session_state.storage_size = get_storage_size()
    st.session_state.storage_last_updated = current_time
```

### Storage Limit Enforcement

```python
storage_percent = get_storage_percent()
storage_full = storage_percent >= 95

# Disable indexing if storage full
index_button = st.button(
    "🚀 Index Repository",
    disabled=st.session_state.is_indexing or not github_url or storage_full
)
```

---

## User Flow

### Scenario 1: Normal Usage (<70% storage)

```
User indexes repo → Storage updates → Green indicator
💾 Storage
✅ 345MB / 1024MB (34%)
[███████░░░░░░░░░░░░░] 34%
```

### Scenario 2: Approaching Limit (80-95%)

```
💾 Storage
⚠️ 850MB / 1024MB (83%)
[████████████████░░░░] 83%

⚠️ Storage at 80%. Consider removing old repos.

🗑️ Clear My Repos (5 repos)
```

### Scenario 3: Storage Full (>95%)

```
💾 Storage
🔴  980MB / 1024MB (96%)
[███████████████████░] 96%

🔗 Index GitHub Repo
🔴 Storage nearly full! Remove repos before indexing new ones.

[Text input disabled]
[🚀 Index Repository - DISABLED]

🗑️ Clear My Repos (8 repos)
```

### Scenario 4: Cleanup Process

```
User clicks "Clear My Repos (3 repos)"
    ↓
⚠️ This will delete 3 repositories. Are you sure?
[✅ Yes, Delete]  [❌ Cancel]
    ↓
User clicks "Yes, Delete"
    ↓
Deleting collections...
    ↓
✅ Deleted 3 repos. Freed 245MB.
    ↓
Storage updates:
💾 Storage
✅ 735MB / 1024MB (72%)
[██████████████░░░░░░] 72%
```

---

## UI Layout

### Sidebar Bottom Section

```
┌─────────────────────────────────────┐
│ 📊 Statistics                       │
│ Messages: 5    Cost: $0.0234        │
│ Model: Claude Haiku                 │
│                                     │
│ ─────────────────────────────       │
│                                     │
│ 🗑️ Clear Conversation               │
│                                     │
│ ─────────────────────────────       │
│                                     │
│ 💾 Storage                          │
│ ✅ 542MB / 1024MB (53%)             │
│ [████████░░░░░░░░░░░░] 53%          │
│                                     │
│ ─────────────────────────────       │
│                                     │
│ 🗑️ Clear My Repos (3 repos)        │
│                                     │
│ ─────────────────────────────       │
│                                     │
│ Made with ❤️ using Claude           │
│ Built by PS2                        │
└─────────────────────────────────────┘
```

### Confirmation Dialog

```
┌─────────────────────────────────────┐
│ ⚠️ This will delete 3 repositories. │
│    Are you sure?                    │
│                                     │
│ ┌─────────────┐ ┌─────────────┐    │
│ │✅ Yes, Delete│ │❌ Cancel    │    │
│ └─────────────┘ └─────────────┘    │
└─────────────────────────────────────┘
```

---

## Storage Calculation Details

### What's Included

- All files in `./chroma_db/` directory
- ChromaDB SQLite database (`chroma.sqlite3`)
- HNSW index files (`.bin` files)
- Metadata files
- All collections (permanent + user-indexed)

### What's Not Included

- Temporary clone directories (deleted after indexing)
- Source code files
- Application code

### Typical Storage Usage

| Item | Size |
|------|------|
| Empty ChromaDB | ~1MB |
| Permanent repos (4) | ~300-400MB |
| User repo (small) | ~50-100MB |
| User repo (medium) | ~100-200MB |
| User repo (large) | ~200-400MB |

---

## Performance Considerations

### Caching Strategy

**Problem:** Calculating directory size is expensive (walks entire tree)

**Solution:** Cache for 30 seconds
- First access: Calculate and cache
- Subsequent accesses: Use cached value
- After 30s: Recalculate

**Benefits:**
- Reduces I/O operations
- Improves UI responsiveness
- Still reasonably accurate

### When Storage Updates

Storage is recalculated:
1. Every 30 seconds (automatic)
2. After indexing new repo
3. After deleting repos
4. On manual refresh (if implemented)

---

## Error Handling

### Scenario 1: Permission Errors

```python
try:
    if os.path.exists(fp):
        total += os.path.getsize(fp)
except (OSError, PermissionError):
    continue  # Skip inaccessible files
```

### Scenario 2: Collection Deletion Fails

```python
try:
    client.delete_collection(col.name)
    deleted_count += 1
except Exception as e:
    return {
        "status": "error",
        "message": str(e),
        "count": 0
    }
```

### Scenario 3: ChromaDB Connection Issues

```python
try:
    client = chromadb.PersistentClient(path="./chroma_db")
except Exception as e:
    st.error(f"❌ Cannot connect to database: {e}")
```

---

## Configuration

### Storage Limit

Default: **1024MB (1GB)**

To change:
```python
max_storage = 2048  # 2GB
storage_percent = (storage_size / max_storage) * 100
```

### Warning Thresholds

```python
# 80% warning
if storage_percent >= 80:
    st.warning("⚠️ Storage at 80%...")

# 95% critical
if storage_percent >= 95:
    st.error("🔴 Storage nearly full!")
    disable_indexing = True
```

### Cache Duration

Default: **30 seconds**

To change:
```python
CACHE_DURATION = 60  # 60 seconds

if current_time - st.session_state.storage_last_updated > CACHE_DURATION:
    st.session_state.storage_size = get_storage_size()
```

---

## Future Enhancements

### Potential Improvements

1. **Selective Deletion**
   - Choose which repos to delete
   - Delete individual repos instead of all

2. **Storage Analytics**
   - Show size per repository
   - Sort by size, date indexed
   - Identify largest repos

3. **Auto-Cleanup**
   - Delete oldest repos when limit reached
   - LRU (Least Recently Used) eviction

4. **Compression**
   - Compress old collections
   - Archive unused repos

5. **Cloud Storage**
   - Upload to S3/GCS
   - Offload to external storage

6. **Storage Quotas**
   - Per-user limits
   - Premium users get more storage

---

## Troubleshooting

### Issue: Storage shows 0MB

**Cause:** ChromaDB directory doesn't exist

**Solution:** Index a repository first

### Issue: Storage not updating

**Cause:** Cache not expiring

**Solution:** Wait 30 seconds or refresh page

### Issue: Cleanup doesn't free space

**Cause:** Collections not actually deleted

**Solution:** Check ChromaDB logs, verify permissions

### Issue: Can't index new repos at 80%

**Cause:** Only blocks at 95%

**Solution:** This is a warning, not a block. Continue indexing or cleanup.

---

## Summary

✅ **Real-time storage monitoring**  
✅ **Color-coded status indicators**  
✅ **Automatic capacity warnings**  
✅ **One-click cleanup**  
✅ **Confirmation before deletion**  
✅ **Efficient caching (30s)**  
✅ **Prevents over-storage**  
✅ **Clear user feedback**  

Users can now monitor and manage their storage effectively! 💾

---

**Status**: ✅ Complete  
**Files Modified**: 1 (`app.py`)  
**New Functions**: 4  
**New Session State**: 2  
**Lines Added**: ~150  
**Storage Limit**: 1GB  
**Cache Duration**: 30 seconds  

