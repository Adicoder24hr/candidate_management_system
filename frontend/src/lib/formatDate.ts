import { parseISO } from 'date-fns';
import { format, toZonedTime } from 'date-fns-tz';

const IST = 'Asia/Kolkata';

/**
 * Format an ISO UTC timestamp to IST like "08 Oct 2026, 10:30 AM"
 */
export function formatIST(isoString: string): string {
  try {
    const utcDate = parseISO(isoString);
    const zonedDate = toZonedTime(utcDate, IST);
    return format(zonedDate, 'dd MMM yyyy, hh:mm aa', { timeZone: IST });
  } catch {
    return isoString;
  }
}

/**
 * Format to short date "DD-MM-YYYY" in IST
 */
export function formatISTDate(isoString: string): string {
  try {
    const utcDate = parseISO(isoString);
    const zonedDate = toZonedTime(utcDate, IST);
    return format(zonedDate, 'dd-MM-yyyy', { timeZone: IST });
  } catch {
    return isoString;
  }
}
