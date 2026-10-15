'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Checkbox,
  Paper,
  TextField,
  InputAdornment,
  Skeleton,
  CircularProgress,
  Alert,
  Snackbar,
  IconButton,
  Tooltip,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import HistoryIcon from '@mui/icons-material/History';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';

import { StatusChip } from '@/components/StatusChip';
import { AddCandidateDialog } from '@/components/AddCandidateDialog';
import { SendMessageDrawer } from '@/components/SendMessageDrawer';
import { HistoryDrawer } from '@/components/HistoryDrawer';
import { BulkResultsDialog } from '@/components/BulkResultsDialog';
import {
  fetchCandidates,
  Candidate,
  BulkSendResponse,
  bulkDeleteCandidates,
  fetchProviderHealth,
  ProviderHealth,
} from '@/lib/api';

type SortField = 'name' | 'phone' | 'created_at';
type SortDir = 'asc' | 'desc';

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debouncedValue;
}

export default function CandidatePage() {
  // Data state
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState('');
  const [providerHealth, setProviderHealth] = useState<ProviderHealth | null>(null);

  // Table controls
  const [searchInput, setSearchInput] = useState('');
  const debouncedSearch = useDebounce(searchInput, 350);
  const [page, setPage] = useState(0);       // 0-indexed for MUI
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  // Selection
  const [selected, setSelected] = useState<Set<string>>(new Set());

  // Dialogs/Drawers
  const [addCandidateOpen, setAddCandidateOpen] = useState(false);
  const [sendOpen, setSendOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyCandidate, setHistoryCandidate] = useState<Candidate | null>(null);
  const [bulkResultOpen, setBulkResultOpen] = useState(false);
  const [bulkResult, setBulkResult] = useState<BulkSendResponse | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Snackbar
  const [snack, setSnack] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  function showSnack(message: string, severity: 'success' | 'error' = 'success') {
    setSnack({ open: true, message, severity });
  }

  // ─── Fetch candidates ────────────────────────────────────────────────────────
  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setFetchError('');
    try {
      const ordering = `${sortDir === 'desc' ? '-' : ''}${sortField}`;
      const data = await fetchCandidates({
        search: debouncedSearch || undefined,
        page: page + 1,
        page_size: rowsPerPage,
        ordering,
      });
      setCandidates(data.results);
      setTotalCount(data.count);
    } catch {
      setFetchError('Failed to load candidates. Please retry.');
    } finally {
      if (!silent) setLoading(false);
    }
  }, [debouncedSearch, page, rowsPerPage, sortField, sortDir]);

  useEffect(() => {
    load(false);
  }, [load]);

  useEffect(() => {
    let active = true;
    const refreshHealth = async () => {
      try {
        const health = await fetchProviderHealth();
        if (active) setProviderHealth(health);
      } catch {
        if (active) setProviderHealth({ status: 'down', provider_reachable: false, sent: 0, delivered: 0, failed: 0, success_rate: null, recent_failure_rate: 0 });
      }
    };
    void refreshHealth();
    const timer = setInterval(refreshHealth, 15000);
    return () => { active = false; clearInterval(timer); };
  }, []);

  // Reset page to 0 when search changes
  useEffect(() => {
    setPage(0);
    setSelected(new Set());
  }, [debouncedSearch]);

  // ─── Sort ────────────────────────────────────────────────────────────────────
  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('asc');
    }
    setPage(0);
  }

  // ─── Selection ───────────────────────────────────────────────────────────────
  function toggleSelect(id: string) {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleSelectAll() {
    if (selected.size === candidates.length && candidates.length > 0) {
      setSelected(new Set());
    } else {
      setSelected(new Set(candidates.map(c => c.candidate_id)));
    }
  }

  const allSelected = candidates.length > 0 && selected.size === candidates.length;
  const someSelected = selected.size > 0 && !allSelected;
  const selectedCandidates = candidates.filter(c => selected.has(c.candidate_id));

  // ─── Send message ─────────────────────────────────────────────────────────────
  function openSend() {
    if (selected.size === 0) return;
    setSendOpen(true);
  }

  function handleSendSuccess(result: BulkSendResponse) {
    if (result.total > 1 || result.failed > 0) {
      setBulkResult(result);
      setBulkResultOpen(true);
    }
    setSelected(new Set());
    load(true);
    if (result.failed === 0) {
      showSnack(`Message sent to ${result.succeeded} candidate${result.succeeded !== 1 ? 's' : ''}.`);
    }
  }

  // ─── History ─────────────────────────────────────────────────────────────────
  function openHistory(candidate: Candidate) {
    setHistoryCandidate(candidate);
    setHistoryOpen(true);
  }

  async function confirmDelete() {
    const count = selected.size;
    setDeleting(true);
    try {
      await bulkDeleteCandidates(Array.from(selected));
      setDeleteOpen(false);
      setSelected(new Set());
      showSnack(`${count} candidate${count === 1 ? '' : 's'} deleted.`);
      await load(true);
    } catch {
      showSnack('Could not delete candidates. Please try again.', 'error');
    } finally {
      setDeleting(false);
    }
  }

  // ─── Add candidate success ────────────────────────────────────────────────────
  function handleAddSuccess() {
    showSnack('Candidate added successfully!');
    load(false);
  }

  const sendLabel = selected.size === 0
    ? 'SEND MESSAGE'
    : `SEND TO ${selected.size} CANDIDATE${selected.size !== 1 ? 'S' : ''}`;

  return (
    <Container maxWidth="xl" sx={{ py: 3, px: { xs: 2, sm: 3 } }}>
      {/* ── Header ── */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 3,
          flexWrap: 'wrap',
          gap: 1,
        }}
      >
        <Typography variant="h1" component="h1">
          Candidate communication
        </Typography>

        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setAddCandidateOpen(true)}
          id="add-candidate-btn"
          aria-label="Add new candidate"
        >
          ADD CANDIDATE
        </Button>
      </Box>

      {providerHealth && (
        <Paper variant="outlined" sx={{ display: 'flex', gap: { xs: 1, sm: 3 }, alignItems: 'center', flexWrap: 'wrap', p: 2, mb: 2 }} aria-live="polite">
          <Typography variant="subtitle1" fontWeight={600}>Communication service</Typography>
          <Typography color={providerHealth.status === 'operational' ? 'success.main' : providerHealth.status === 'degraded' ? 'warning.main' : 'error.main'} fontWeight={600}>
            {providerHealth.status === 'operational' ? 'Operational' : providerHealth.status === 'degraded' ? 'Degraded' : 'Down'}
          </Typography>
          <Typography variant="body2">Sent {providerHealth.sent}</Typography>
          <Typography variant="body2">Delivered {providerHealth.delivered}</Typography>
          <Typography variant="body2">Failed {providerHealth.failed}</Typography>
          <Typography variant="body2">Success rate {providerHealth.success_rate === null ? '-' : `${providerHealth.success_rate}%`}</Typography>
        </Paper>
      )}
      {providerHealth?.status === 'down' && (
        <Alert severity="error" sx={{ mb: 2 }}>The messaging service is currently unavailable. Sending is disabled until it recovers.</Alert>
      )}

      {/* ── Toolbar: search + send button ── */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          mb: 2,
          flexWrap: 'wrap',
        }}
      >
        <TextField
          id="candidate-search"
          placeholder="Search by name, phone, or email…"
          size="small"
          value={searchInput}
          onChange={e => setSearchInput(e.target.value)}
          inputProps={{ 'aria-label': 'Search candidates' }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: 'text.secondary' }} />
              </InputAdornment>
            ),
          }}
          sx={{ minWidth: 280, flex: 1, maxWidth: 420 }}
        />

        <Box sx={{ ml: 'auto', display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteOutlineIcon />}
            disabled={selected.size === 0}
            onClick={() => setDeleteOpen(true)}
            aria-label={`Delete ${selected.size} selected candidates`}
          >
            DELETE{selected.size ? ` ${selected.size} CANDIDATE${selected.size === 1 ? '' : 'S'}` : ''}
          </Button>
          <Tooltip title="Refresh">
            <IconButton onClick={() => load(false)} aria-label="Refresh candidates" id="refresh-btn">
              <RefreshIcon />
            </IconButton>
          </Tooltip>

          <Button
            variant="contained"
            disabled={selected.size === 0 || providerHealth?.status === 'down'}
            onClick={openSend}
            id="send-message-btn"
            aria-label={sendLabel}
          >
            {sendLabel}
          </Button>
        </Box>
      </Box>

      {/* ── Fetch error ── */}
      {fetchError && (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          action={
            <Button size="small" onClick={() => load(false)} startIcon={<RefreshIcon />}>
              Retry
            </Button>
          }
        >
          {fetchError}
        </Alert>
      )}

      {/* ── Candidate Table ── */}
      <Paper variant="outlined" sx={{ borderRadius: 2, overflow: 'hidden' }}>
        <TableContainer>
          <Table aria-label="Candidate list table" size="medium" sx={{ tableLayout: 'fixed', width: '100%', '& .MuiTableCell-root': { px: { xs: 0.5, sm: 2 } } }}>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox" sx={{ width: 52 }}>
                  <Checkbox
                    indeterminate={someSelected}
                    checked={allSelected}
                    onChange={toggleSelectAll}
                    aria-label="Select all candidates"
                    id="select-all-candidates"
                    disabled={loading || candidates.length === 0}
                  />
                </TableCell>

                <TableCell sx={{ width: { xs: 100, sm: 180 } }}>
                  <TableSortLabel
                    active={sortField === 'name'}
                    direction={sortField === 'name' ? sortDir : 'asc'}
                    onClick={() => handleSort('name')}
                    aria-label="Sort by name"
                  >
                    Full name
                  </TableSortLabel>
                </TableCell>

                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' }, width: { sm: 170 } }}>
                  <TableSortLabel
                    active={sortField === 'phone'}
                    direction={sortField === 'phone' ? sortDir : 'asc'}
                    onClick={() => handleSort('phone')}
                    aria-label="Sort by mobile number"
                  >
                    Mobile number
                  </TableSortLabel>
                </TableCell>

                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' }, width: 130 }}>Last message</TableCell>
                <TableCell sx={{ width: { xs: 82, sm: 120 } }}>Status</TableCell>
                <TableCell sx={{ width: { xs: 48, sm: 80 } }}>Actions</TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {loading ? (
                Array.from({ length: rowsPerPage }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell padding="checkbox"><Skeleton variant="rectangular" width={20} height={20} /></TableCell>
                    <TableCell><Skeleton width="60%" /></TableCell>
                    <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}><Skeleton width="50%" /></TableCell>
                    <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}><Skeleton width="40%" /></TableCell>
                    <TableCell><Skeleton width={72} /></TableCell>
                    <TableCell><Skeleton width={80} /></TableCell>
                  </TableRow>
                ))
              ) : candidates.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 8 }}>
                    <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 500 }}>
                      {debouncedSearch ? `No candidates match "${debouncedSearch}"` : 'No candidates yet'}
                    </Typography>
                    {!debouncedSearch && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                        Click &quot;+ ADD CANDIDATE&quot; to add your first candidate.
                      </Typography>
                    )}
                  </TableCell>
                </TableRow>
              ) : (
                candidates.map(candidate => {
                  const isSelected = selected.has(candidate.candidate_id);
                  return (
                    <TableRow
                      key={candidate.candidate_id}
                      hover
                      selected={isSelected}
                      sx={{
                        cursor: 'pointer',
                        '&.Mui-selected': { backgroundColor: 'primary.light' },
                        '&.Mui-selected:hover': { backgroundColor: 'primary.light' },
                      }}
                      onClick={() => toggleSelect(candidate.candidate_id)}
                      aria-selected={isSelected}
                    >
                      <TableCell padding="checkbox" onClick={e => e.stopPropagation()}>
                        <Checkbox
                          checked={isSelected}
                          onChange={() => toggleSelect(candidate.candidate_id)}
                          aria-label={`Select ${candidate.name}`}
                          id={`select-${candidate.candidate_id}`}
                        />
                      </TableCell>

                      <TableCell>
                        <Button
                          variant="text"
                          onClick={(event) => { event.stopPropagation(); openHistory(candidate); }}
                          aria-label={`View communication history for ${candidate.name}`}
                          sx={{ p: 0, minWidth: 0, color: 'primary.main', fontWeight: 500, '&:hover': { textDecoration: 'underline', backgroundColor: 'transparent' } }}
                        >
                          <Box component="span" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                            {candidate.name}
                            <Typography component="span" variant="caption" sx={{ display: { xs: 'block', sm: 'none' }, color: 'text.secondary' }}>
                              {candidate.phone}
                            </Typography>
                          </Box>
                        </Button>
                      </TableCell>

                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                        <Typography variant="body1">{candidate.phone}</Typography>
                      </TableCell>

                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                        {candidate.last_message === 'NA' ? (
                          <Typography variant="body2" color="text.secondary">NA</Typography>
                        ) : (
                          <Typography variant="body2">{candidate.last_message}</Typography>
                        )}
                      </TableCell>

                      <TableCell><StatusChip statusRaw={candidate.status_raw} /></TableCell>

                      <TableCell onClick={e => e.stopPropagation()}>
                        <Tooltip title="View communication history">
                          <IconButton
                            size="small"
                            onClick={() => openHistory(candidate)}
                            aria-label={`View history for ${candidate.name}`}
                            id={`history-${candidate.candidate_id}`}
                          >
                            <HistoryIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <TablePagination
          component="div"
          count={totalCount}
          page={page}
          onPageChange={(_e, newPage) => { setPage(newPage); setSelected(new Set()); }}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={e => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
            setSelected(new Set());
          }}
          rowsPerPageOptions={[10, 25, 50]}
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} of ${count}`}
          labelRowsPerPage="Rows per page:"
          aria-label="Candidate table pagination"
        />
      </Paper>

      {/* ── Dialogs & Drawers ── */}
      <AddCandidateDialog
        open={addCandidateOpen}
        onClose={() => setAddCandidateOpen(false)}
        onSuccess={handleAddSuccess}
      />

      <SendMessageDrawer
        open={sendOpen}
        candidates={selectedCandidates}
        onClose={() => setSendOpen(false)}
        onSuccess={handleSendSuccess}
      />

      <HistoryDrawer
        open={historyOpen}
        candidateId={historyCandidate?.candidate_id ?? null}
        candidateName={historyCandidate?.name ?? ''}
        candidatePhone={historyCandidate?.phone ?? ''}
        candidateEmail={historyCandidate?.email ?? ''}
        onClose={() => { setHistoryOpen(false); setHistoryCandidate(null); }}
      />

      <BulkResultsDialog
        open={bulkResultOpen}
        result={bulkResult}
        onClose={() => setBulkResultOpen(false)}
      />

      <Dialog open={deleteOpen} onClose={() => !deleting && setDeleteOpen(false)}>
        <DialogTitle>Delete candidate{selected.size === 1 ? '' : 's'}?</DialogTitle>
        <DialogContent>
          <Typography>
            {selected.size === 1
              ? `Delete ${selectedCandidates[0]?.name ?? 'this candidate'}? Their communication history will be preserved.`
              : `Delete these ${selected.size} candidates? Their communication history will be preserved.`}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteOpen(false)} disabled={deleting}>Cancel</Button>
          <Button color="error" variant="contained" onClick={confirmDelete} disabled={deleting}>
            {deleting ? <CircularProgress size={18} color="inherit" /> : `DELETE ${selected.size} CANDIDATE${selected.size === 1 ? '' : 'S'}`}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snack.open}
        autoHideDuration={4000}
        onClose={() => setSnack(s => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        aria-live="polite"
      >
        <Alert
          onClose={() => setSnack(s => ({ ...s, open: false }))}
          severity={snack.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snack.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}
