'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  CircularProgress,
  Divider,
  Button,
  Alert,
  Tooltip,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import RefreshIcon from '@mui/icons-material/Refresh';
import ReplayIcon from '@mui/icons-material/Replay';
import { StatusChip } from './StatusChip';
import { fetchCandidateHistory, retryMessage, MessageHistoryItem } from '@/lib/api';
import { formatIST } from '@/lib/formatDate';

interface HistoryDrawerProps {
  open: boolean;
  candidateId: string | null;
  candidateName: string;
  candidatePhone: string;
  candidateEmail: string;
  onClose: () => void;
}

const TERMINAL_STATUSES = new Set(['read', 'failed']);
const POLL_INTERVAL = 3000;

export function HistoryDrawer({ open, candidateId, candidateName, candidatePhone, candidateEmail, onClose }: HistoryDrawerProps) {
  const [history, setHistory] = useState<MessageHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async (silent = false) => {
    if (!candidateId) return;
    if (!silent) setLoading(true);
    setError('');
    try {
      const data = await fetchCandidateHistory(candidateId);
      setHistory(data);
    } catch {
      setError('Failed to load communication history. Please retry.');
    } finally {
      if (!silent) setLoading(false);
    }
  }, [candidateId]);

  // Poll every 3s while any non-terminal status is visible
  useEffect(() => {
    if (!open || !candidateId) return;
    load(false);

    function scheduleNext() {
      pollRef.current = setTimeout(async () => {
        await load(true);
        // After load, check if still polling needed
        setHistory(prev => {
          const hasNonTerminal = prev.some(h => !TERMINAL_STATUSES.has(h.status_raw));
          if (hasNonTerminal) scheduleNext();
          return prev;
        });
      }, POLL_INTERVAL);
    }

    scheduleNext();

    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, [open, candidateId, load]);

  async function handleRetry(recipientId: string) {
    setRetryingId(recipientId);
    try {
      const result = await retryMessage(recipientId);
      if (result.error) {
        // Show brief error but continue
      }
      await load(true);
    } finally {
      setRetryingId(null);
    }
  }

  const isEmpty = !loading && history.length === 0 && !error;

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        '& .MuiDrawer-paper': {
          width: { xs: '100%', sm: 480 },
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 3, py: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box>
          <Typography variant="h2" component="h2">Communication History</Typography>
          {candidateName && (
            <Box sx={{ mt: 0.5 }}>
              <Typography variant="body2" color="text.secondary">{candidateName} · {candidateId}</Typography>
              <Typography variant="body2" color="text.secondary">{candidatePhone}</Typography>
              <Typography variant="body2" color="text.secondary">{candidateEmail}</Typography>
            </Box>
          )}
        </Box>
        <IconButton aria-label="close history panel" onClick={onClose}>
          <CloseIcon />
        </IconButton>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, overflowY: 'auto', px: 3, py: 2 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', pt: 6 }}>
            <CircularProgress size={32} aria-label="Loading history" />
          </Box>
        ) : error ? (
          <Alert
            severity="error"
            action={
              <Button size="small" onClick={() => load(false)} startIcon={<RefreshIcon />}>
                Retry
              </Button>
            }
          >
            {error}
          </Alert>
        ) : isEmpty ? (
          <Box sx={{ textAlign: 'center', py: 8, color: 'text.secondary' }}>
            <Typography variant="body1" sx={{ fontWeight: 500 }}>No messages yet</Typography>
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              Select this candidate and click &quot;Send Message&quot; to get started.
            </Typography>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {history.map((item, idx) => (
              <React.Fragment key={item.recipient_id}>
                <HistoryItem
                  item={item}
                  isRetrying={retryingId === item.recipient_id}
                  onRetry={() => handleRetry(item.recipient_id)}
                />
                {idx < history.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </Box>
        )}
      </Box>
    </Drawer>
  );
}

// ─── Single history item ───────────────────────────────────────────────────────

function HistoryItem({
  item,
  isRetrying,
  onRetry,
}: {
  item: MessageHistoryItem;
  isRetrying: boolean;
  onRetry: () => void;
}) {
  const isPermanentFailure = item.status_raw === 'failed' && !item.retryable;
  const isRetryableFailure = item.status_raw === 'failed' && item.retryable;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      {/* Message text */}
      <Typography variant="body1" sx={{ lineHeight: 1.5, wordBreak: 'break-word' }}>
        {item.message_body}
      </Typography>

      {/* Timestamp + status row */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
        <Typography variant="body2" color="text.secondary">
          {formatIST(item.created_at)}
        </Typography>
        <StatusChip statusRaw={item.status_raw} />
      </Box>

      {/* Failure reason */}
      {item.status_raw === 'failed' && item.friendly_message && (
        <Typography variant="body2" color="error.main" sx={{ mt: 0.5 }}>
          {isPermanentFailure
            ? `Can't be retried: ${item.friendly_message}`
            : item.friendly_message}
        </Typography>
      )}

      {/* Retry button (retryable only) */}
      {isRetryableFailure && (
        <Box sx={{ mt: 0.5 }}>
          <Button
            size="small"
            variant="outlined"
            color="error"
            startIcon={isRetrying ? <CircularProgress size={14} color="inherit" /> : <ReplayIcon />}
            onClick={onRetry}
            disabled={isRetrying}
            aria-label={`Retry sending message`}
            id={`retry-${item.recipient_id}`}
          >
            {isRetrying ? 'Retrying…' : 'Retry'}
          </Button>
        </Box>
      )}

      {/* Attempt count */}
      {item.attempt_count > 1 && (
        <Typography variant="body2" color="text.secondary">
          Attempt {item.attempt_count}
        </Typography>
      )}
    </Box>
  );
}
