'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  CircularProgress,
  Alert,
  IconButton,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { createCandidate } from '@/lib/api';

interface AddCandidateDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface FormState {
  name: string;
  phone: string;
  email: string;
}

interface FormErrors {
  name?: string;
  phone?: string;
  email?: string;
  general?: string;
}

export function AddCandidateDialog({ open, onClose, onSuccess }: AddCandidateDialogProps) {
  const [form, setForm] = useState<FormState>({ name: '', phone: '', email: '' });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);

  function handleChange(field: keyof FormState) {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setForm(prev => ({ ...prev, [field]: e.target.value }));
      setErrors(prev => ({ ...prev, [field]: undefined, general: undefined }));
    };
  }

  function validateLocally(): FormErrors {
    const errs: FormErrors = {};
    if (!form.name.trim()) {
      errs.name = 'Candidate name is required.';
    } else if (form.name.trim().length < 2 || form.name.trim().length > 80) {
      errs.name = 'Name must be between 2 and 80 characters.';
    }
    if (!form.phone.trim()) {
      errs.phone = 'Mobile number is required.';
    } else if (!/^\+?[0-9][0-9\s()-]{6,24}$/.test(form.phone.trim())) {
      errs.phone = 'Enter a valid phone number.';
    }
    if (!form.email.trim()) {
      errs.email = 'Email is required.';
    } else if (!/^[\w.-]+@[\w.-]+\.\w+$/.test(form.email.trim())) {
      errs.email = 'Please enter a valid email address.';
    }
    return errs;
  }

  const isFormValid = Object.keys(validateLocally()).length === 0;

  async function handleSubmit() {
    const localErrors = validateLocally();
    if (Object.keys(localErrors).length > 0) {
      setErrors(localErrors);
      return;
    }

    setLoading(true);
    setErrors({});
    try {
      const result = await createCandidate({
        name: form.name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim().toLowerCase(),
      });

      if (result.error) {
        const apiErr = result.error.error;
        if (apiErr.fields) {
          setErrors(apiErr.fields as FormErrors);
        } else {
          setErrors({ general: apiErr.message });
        }
      } else {
        // Success
        setForm({ name: '', phone: '', email: '' });
        setErrors({});
        onSuccess();
        onClose();
      }
    } catch {
      setErrors({ general: 'Something went wrong. Please try again.' });
    } finally {
      setLoading(false);
    }
  }

  function handleClose() {
    if (loading) return;
    setForm({ name: '', phone: '', email: '' });
    setErrors({});
    onClose();
  }

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="add-candidate-dialog-title"
    >
      <DialogTitle id="add-candidate-dialog-title" sx={{ fontWeight: 600, pb: 1 }}>
        Add Candidate
        <IconButton
          aria-label="close dialog"
          onClick={handleClose}
          disabled={loading}
          sx={{ position: 'absolute', right: 8, top: 8 }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          {errors.general && (
            <Alert severity="error" sx={{ mb: 0 }}>
              {errors.general}
            </Alert>
          )}

          <TextField
            id="candidate-name"
            label="Candidate Name"
            required
            value={form.name}
            onChange={handleChange('name')}
            error={!!errors.name}
            helperText={errors.name}
            disabled={loading}
            inputProps={{ 'aria-label': 'Candidate name', maxLength: 80 }}
            fullWidth
          />

          <TextField
            id="candidate-phone"
            label="Mobile Number"
            required
            value={form.phone}
            onChange={handleChange('phone')}
            error={!!errors.phone}
            helperText={errors.phone || 'E.g. +919876543210 or 09876543210'}
            disabled={loading}
            inputProps={{ 'aria-label': 'Mobile number' }}
            fullWidth
          />

          <TextField
            id="candidate-email"
            label="Email"
            type="email"
            required
            value={form.email}
            onChange={handleChange('email')}
            error={!!errors.email}
            helperText={errors.email}
            disabled={loading}
            inputProps={{ 'aria-label': 'Email address' }}
            fullWidth
          />
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button variant="text" onClick={handleClose} disabled={loading} id="cancel-add-candidate">
          CANCEL
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading || !isFormValid}
          id="submit-add-candidate"
          sx={{ minWidth: 140 }}
        >
          {loading ? <CircularProgress size={18} color="inherit" /> : 'ADD CANDIDATE'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
