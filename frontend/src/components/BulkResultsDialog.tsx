'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  Alert,
  LinearProgress,
  Divider,
} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import { BulkSendResponse, BulkSendResult } from '@/lib/api';

interface BulkResultsDialogProps {
  open: boolean;
  result: BulkSendResponse | null;
  onClose: () => void;
}

export function BulkResultsDialog({ open, result, onClose }: BulkResultsDialogProps) {
  if (!result) return null;

  const allSucceeded = result.failed === 0;
  const successRate = result.total > 0 ? (result.succeeded / result.total) * 100 : 0;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="bulk-results-title"
    >
      <DialogTitle id="bulk-results-title" sx={{ fontWeight: 600 }}>
        {allSucceeded ? '✓ Messages Sent' : 'Send Results'}
      </DialogTitle>

      <DialogContent>
        {/* Summary */}
        <Box sx={{ mb: 2 }}>
          {allSucceeded ? (
            <Alert severity="success" icon={<CheckCircleOutlineIcon />}>
              All {result.succeeded} message{result.succeeded !== 1 ? 's' : ''} sent successfully.
            </Alert>
          ) : (
            <>
              <Alert severity={result.succeeded === 0 ? 'error' : 'warning'} sx={{ mb: 1 }}>
                {result.succeeded} succeeded, {result.failed} failed
              </Alert>
              <LinearProgress
                variant="determinate"
                value={successRate}
                color={successRate >= 50 ? 'success' : 'error'}
                sx={{ borderRadius: 4, height: 6 }}
              />
            </>
          )}
        </Box>

        {/* Per-candidate result list */}
        {!allSucceeded && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, maxHeight: 320, overflowY: 'auto' }}>
            {result.results.map((r, idx) => (
              <React.Fragment key={`${r.candidate_id}-${idx}`}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                  {r.status === 'sent' ? (
                    <CheckCircleOutlineIcon color="success" sx={{ mt: 0.25 }} />
                  ) : (
                    <ErrorOutlineIcon color="error" sx={{ mt: 0.25 }} />
                  )}
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {r.candidate_name}
                    </Typography>
                    {r.status === 'failed' && r.error && (
                      <Typography variant="body2" color="error.main">
                        {r.error}
                      </Typography>
                    )}
                  </Box>
                  <Chip
                    label={r.status === 'sent' ? 'Sent' : 'Failed'}
                    size="small"
                    color={r.status === 'sent' ? 'success' : 'error'}
                    variant="outlined"
                  />
                </Box>
                {idx < result.results.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button variant="contained" onClick={onClose} id="bulk-results-close">
          DONE
        </Button>
      </DialogActions>
    </Dialog>
  );
}
