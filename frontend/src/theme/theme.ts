import { createTheme } from '@mui/material/styles';

declare module '@mui/material/styles' {
  interface Palette {
    status: {
      readBg: string;
      readText: string;
      deliveredBg: string;
      deliveredText: string;
      sentBg: string;
      sentText: string;
      failedBg: string;
      failedText: string;
      naText: string;
      queuedBg: string;
      queuedText: string;
      scheduledBg: string;
      scheduledText: string;
      neutralBg: string;
      neutralText: string;
    };
    tableHighlight: string;
    toastSuccessBg: string;
    toastSuccessText: string;
  }
  interface PaletteOptions {
    status?: {
      readBg?: string;
      readText?: string;
      deliveredBg?: string;
      deliveredText?: string;
      sentBg?: string;
      sentText?: string;
      failedBg?: string;
      failedText?: string;
      naText?: string;
      queuedBg?: string;
      queuedText?: string;
      scheduledBg?: string;
      scheduledText?: string;
      neutralBg?: string;
      neutralText?: string;
    };
    tableHighlight?: string;
    toastSuccessBg?: string;
    toastSuccessText?: string;
  }
}

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976D2',
      dark: '#1565C0',
      light: '#EBF3FE',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#D32F2F',
      dark: '#C62828',
      light: '#FFEBEE',
      contrastText: '#FFFFFF',
    },
    success: {
      main: '#2E7D32',
      dark: '#1B5E20',
      light: '#E8F5E9',
      contrastText: '#FFFFFF',
    },
    text: {
      primary: '#1E293B',
      secondary: '#64748B',
    },
    divider: '#E0E0E0',
    background: {
      default: '#F8FAFC',
      paper: '#FFFFFF',
    },
    status: {
      readBg: '#E8F5E9',
      readText: '#2E7D32',
      deliveredBg: '#E0F2F1',
      deliveredText: '#00796B',
      sentBg: '#E3F2FD',
      sentText: '#1976D2',
      failedBg: '#FFEBEE',
      failedText: '#D32F2F',
      naText: '#757575',
      queuedBg: '#FFF8E1',
      queuedText: '#F57F17',
      scheduledBg: '#EDE7F6',
      scheduledText: '#512DA8',
      neutralBg: '#F5F5F5',
      neutralText: '#616161',
    },
    tableHighlight: '#EBF3FE',
    toastSuccessBg: '#EDF7ED',
    toastSuccessText: '#1E4620',
  },
  typography: {
    fontFamily: ['Inter', 'Roboto', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'].join(','),
    h1: {
      fontSize: '20px',
      fontWeight: 600,
      lineHeight: '28px',
      letterSpacing: '-0.01em',
    },
    h2: {
      fontSize: '18px',
      fontWeight: 600,
      lineHeight: '24px',
    },
    body1: {
      fontSize: '14px',
      lineHeight: '20px',
    },
    body2: {
      fontSize: '13px',
      lineHeight: '18px',
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
      fontSize: '14px',
    },
  },
  shape: {
    borderRadius: 8,
  },
  spacing: 8,
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      xl: 1536,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          minHeight: '44px', // Touch target >= 44px
          borderRadius: '6px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          padding: '12px 16px',
          borderColor: '#E0E0E0',
          fontSize: '14px',
        },
        head: {
          fontWeight: 600,
          color: '#475569',
          backgroundColor: '#F8FAFC',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          fontWeight: 500,
        },
      },
    },
  },
});
