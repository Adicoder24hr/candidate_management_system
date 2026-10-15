'use client';

import React, { useState, useRef, useLayoutEffect } from 'react';
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Chip,
  Button,
  TextField,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import SendIcon from '@mui/icons-material/Send';
import { Candidate, BulkSendResponse, BulkSendResult } from '@/lib/api';
import { sendMessage, sendSingleMessage } from '@/lib/api';

interface SendMessageDrawerProps {
  open: boolean;
  candidates: Candidate[];   // selected candidates to send to
  onClose: () => void;
  onSuccess: (result: BulkSendResponse) => void;
}

export function SendMessageDrawer({
  open,
  candidates,
  onClose,
  onSuccess,
}: SendMessageDrawerProps) {
  const [body, setBody] = useState('');
  const [bodyError, setBodyError] = useState('');
  const [loading, setLoading] = useState(false);
  const [generalError, setGeneralError] = useState('');
  const chipContainerRef = useRef<HTMLDivElement>(null);
  const [overflowCount, setOverflowCount] = useState(0);
  const [visibleChips, setVisibleChips] = useState<Candidate[]>(candidates);

  // Measure chip overflow: max 2 rows
  useLayoutEffect(() => {
    if (!open) return;
    setVisibleChips(candidates);
    setOverflowCount(0);

    const container = chipContainerRef.current;
    if (!container || candidates.length === 0) return;

    // We need chips rendered first — so we wait one tick
    requestAnimationFrame(() => {
      if (!container) return;
      const ROW_HEIGHT = 36; // chip height + gap
      const MAX_ROWS = 2;
      const MAX_HEIGHT = ROW_HEIGHT * MAX_ROWS;

      const chipEls = Array.from(container.querySelectorAll('[data-chip]')) as HTMLElement[];
      let firstOverflowIdx = chipEls.length;

      for (let i = 0; i < chipEls.length; i++) {
        if (chipEls[i].offsetTop > MAX_HEIGHT) {
          firstOverflowIdx = i;
          break;
        }
      }

      if (firstOverflowIdx < chipEls.length) {
        setVisibleChips(candidates.slice(0, firstOverflowIdx));
        setOverflowCount(candidates.length - firstOverflowIdx);
      }
    });
  }, [open, candidates]);

  async function handleSend() {
    if (!body.trim()) {
      setBodyError('Message is required.');
      return;
    }
    setLoading(true);
    setBodyError('');
    setGeneralError('');
    try {
      const result = candidates.length === 1
        ? await sendSingleMessage({ candidate_id: candidates[0].candidate_id, body: body.trim() })
        : await sendMessage({ candidate_ids: candidates.map(c => c.candidate_id), body: body.trim() });
      if (result.error) {
        setGeneralError(result.error.error.message ?? 'Something went wrong.');
      } else if (result.data) {
        const normalizedResult = 'total' in result.data
          ? result.data
          : {
              total: 1,
              succeeded: result.data.status === 'sent' ? 1 : 0,
              failed: result.data.status === 'failed' ? 1 : 0,
              results: [result.data],
            };
        setBody('');
        onSuccess(normalizedResult);
        onClose();
      }
    } catch {
      setGeneralError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  function handleClose() {
    if (loading) return;
    setBody('');
    setBodyError('');
    setGeneralError('');
    onClose();
  }

  const recipientCount = candidates.length;

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={handleClose}
      sx={{
        '& .MuiDrawer-paper': {
          width: { xs: '100%', sm: 560 },
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 3, py: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h2" component="h2">
          Send Message
        </Typography>
        <IconButton aria-label="close send message panel" onClick={handleClose} disabled={loading}>
          <CloseIcon />
        </IconButton>
      </Box>

      {/* Body */}
      <Box sx={{ flex: 1, overflowY: 'auto', px: 3, py: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Recipients */}
        <Box>
          <Typography variant="body1" sx={{ fontWeight: 500, mb: 1 }}>
            {recipientCount === 1 ? '1 Recipient' : `${recipientCount} Recipients`}
          </Typography>
          <Box
            ref={chipContainerRef}
            sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, overflow: 'hidden', maxHeight: '80px' }}
          >
            {visibleChips.map(c => (
              <Chip
                key={c.candidate_id}
                data-chip
                label={c.name}
                size="small"
                sx={{ borderRadius: '16px' }}
              />
            ))}
            {overflowCount > 0 && (
              <Chip
                label={`+ ${overflowCount}`}
                size="small"
                sx={{ borderRadius: '16px', backgroundColor: 'primary.light', color: 'primary.main' }}
              />
            )}
          </Box>
        </Box>

        <Divider />

        {/* Message textarea */}
        <Box>
          <Typography variant="body1" sx={{ fontWeight: 500, mb: 0.5 }}>
            Message <Box component="span" color="error.main">*</Box>
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Type, or paste the message you want to send.
          </Typography>
          <TextField
            id="send-message-body"
            multiline
            minRows={6}
            fullWidth
            placeholder="Type or paste here..."
            value={body}
            onChange={e => { setBody(e.target.value); setBodyError(''); }}
            error={!!bodyError}
            helperText={bodyError}
            disabled={loading}
            aria-label="Message body"
            inputProps={{ resize: 'vertical' }}
            sx={{ '& textarea': { resize: 'vertical' } }}
          />
        </Box>

        {generalError && (
          <Alert severity="error">{generalError}</Alert>
        )}
      </Box>

      {/* Footer */}
      <Box sx={{ borderTop: '1px solid', borderColor: 'divider', px: 3, py: 2, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Button variant="text" onClick={handleClose} disabled={loading} id="cancel-send-message">
          CANCEL
        </Button>
        <Button
          variant="contained"
          onClick={handleSend}
          disabled={loading || !body.trim()}
          startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <SendIcon />}
          id="confirm-send-message"
          sx={{ minWidth: 160 }}
        >
          {loading ? 'Sending...' : 'SEND MESSAGE'}
        </Button>
      </Box>
    </Drawer>
  );
}
