'use client';

import React from 'react';
import { Chip } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import SendIcon from '@mui/icons-material/Send';
import DoneAllIcon from '@mui/icons-material/DoneAll';
import ScheduleIcon from '@mui/icons-material/Schedule';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { useTheme } from '@mui/material/styles';

interface StatusChipProps {
  statusRaw: string;
}

const STATUS_CONFIG: Record<string, { label: string; icon: React.ReactElement }> = {
  read: {
    label: 'read',
    icon: <VisibilityIcon sx={{ fontSize: '14px !important' }} />,
  },
  delivered: {
    label: 'delivered',
    icon: <DoneAllIcon sx={{ fontSize: '14px !important' }} />,
  },
  sent: {
    label: 'Sent',
    icon: <SendIcon sx={{ fontSize: '14px !important' }} />,
  },
  failed: {
    label: 'Failed',
    icon: <ErrorOutlineIcon sx={{ fontSize: '14px !important' }} />,
  },
  queued: {
    label: 'Queued',
    icon: <HourglassEmptyIcon sx={{ fontSize: '14px !important' }} />,
  },
  scheduled: {
    label: 'Scheduled',
    icon: <ScheduleIcon sx={{ fontSize: '14px !important' }} />,
  },
};

export function StatusChip({ statusRaw }: StatusChipProps) {
  const theme = useTheme();
  const palette = theme.palette.status;
  const config = {
    read: [palette.readBg, palette.readText],
    delivered: [palette.deliveredBg, palette.deliveredText],
    sent: [palette.sentBg, palette.sentText],
    failed: [palette.failedBg, palette.failedText],
    queued: [palette.queuedBg, palette.queuedText],
    scheduled: [palette.scheduledBg, palette.scheduledText],
  } as const;
  if (!statusRaw || statusRaw === 'NA') {
    return <span style={{ color: palette.naText, fontSize: '14px' }}>NA</span>;
  }

  const cfg = STATUS_CONFIG[statusRaw];
  if (!cfg) {
    return (
      <Chip
        label={statusRaw}
        size="small"
        sx={{ backgroundColor: palette.neutralBg, color: palette.neutralText, fontSize: '12px' }}
      />
    );
  }

  const [backgroundColor, color] = config[statusRaw as keyof typeof config];
  return (
    <Chip
      icon={cfg.icon}
      label={cfg.label}
      size="small"
      sx={{
        backgroundColor,
        color,
        fontSize: '12px',
        fontWeight: 500,
        borderRadius: '12px',
        '& .MuiChip-icon': { color },
      }}
    />
  );
}
