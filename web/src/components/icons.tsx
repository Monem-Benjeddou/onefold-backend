import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function Icon({ size = 18, children, ...props }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="square"
      strokeLinejoin="miter"
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      {children}
    </svg>
  );
}

export const CheckIcon = (p: IconProps) => <Icon {...p}><path d="M4 12.5l5 5L20 6.5" /></Icon>;
export const CrossIcon = (p: IconProps) => <Icon {...p}><path d="M6 6l12 12M18 6L6 18" /></Icon>;
export const AlertIcon = (p: IconProps) => <Icon {...p}><path d="M12 3l10 18H2L12 3z" /><path d="M12 10v5M12 18v.5" /></Icon>;
export const InfoIcon = (p: IconProps) => <Icon {...p}><circle cx="12" cy="12" r="9" /><path d="M12 11v6M12 7.5v.5" /></Icon>;
export const LockIcon = (p: IconProps) => <Icon {...p}><rect x="5" y="11" width="14" height="10" /><path d="M8 11V8a4 4 0 018 0v3" /></Icon>;
export const EyeIcon = (p: IconProps) => <Icon {...p}><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></Icon>;
export const EyeOffIcon = (p: IconProps) => <Icon {...p}><path d="M3 3l18 18M10.6 5.1A10.5 10.5 0 0112 5c6.5 0 10 7 10 7a17 17 0 01-3.2 4.2M6.6 6.6A17 17 0 002 12s3.5 7 10 7a9.7 9.7 0 005.4-1.6" /><path d="M9.9 9.9a3 3 0 004.2 4.2" /></Icon>;
export const MailIcon = (p: IconProps) => <Icon {...p}><rect x="3" y="5" width="18" height="14" /><path d="M3 6l9 7 9-7" /></Icon>;
export const ArrowRightIcon = (p: IconProps) => <Icon {...p}><path d="M4 12h15M13 6l6 6-6 6" /></Icon>;
export const ArrowLeftIcon = (p: IconProps) => <Icon {...p}><path d="M20 12H5M11 6l-6 6 6 6" /></Icon>;
export const CopyIcon = (p: IconProps) => <Icon {...p}><rect x="8" y="8" width="13" height="13" /><path d="M16 8V3H3v13h5" /></Icon>;
export const HomeIcon = (p: IconProps) => <Icon {...p}><path d="M3 11l9-7 9 7v10h-6v-6H9v6H3V11z" /></Icon>;
export const PathIcon = (p: IconProps) => <Icon {...p}><circle cx="5" cy="6" r="2" /><circle cx="19" cy="18" r="2" /><path d="M7 6h6a4 4 0 010 8h-2a4 4 0 000 8" /></Icon>;
export const BoxIcon = (p: IconProps) => <Icon {...p}><path d="M3 7l9-4 9 4v10l-9 4-9-4V7z" /><path d="M3 7l9 4 9-4M12 11v10" /></Icon>;
export const LogOutIcon = (p: IconProps) => <Icon {...p}><path d="M15 4h5v16h-5M10 8l-4 4 4 4M6 12h11" /></Icon>;

export function GitHubIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor">
      <path d="M12 .5a11.5 11.5 0 00-3.64 22.41c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.52-1.33-1.28-1.69-1.28-1.69-1.05-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.29 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11 11 0 015.77 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.8 1.19 1.83 1.19 3.09 0 4.42-2.7 5.39-5.26 5.68.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0012 .5z" />
    </svg>
  );
}

export function GoogleIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path fill="#4285F4" d="M23.5 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.45a5.5 5.5 0 01-2.39 3.62v3h3.87c2.26-2.09 3.57-5.16 3.57-8.81z" />
      <path fill="#34A853" d="M12 24c3.24 0 5.96-1.07 7.94-2.91l-3.87-3A7.2 7.2 0 0112 19.25a7.15 7.15 0 01-6.72-4.95h-4v3.09A12 12 0 0012 24z" />
      <path fill="#FBBC05" d="M5.28 14.3a7.2 7.2 0 010-4.6V6.61h-4a12 12 0 000 10.78l4-3.09z" />
      <path fill="#EA4335" d="M12 4.75c1.76 0 3.34.6 4.59 1.8l3.43-3.43A11.5 11.5 0 0012 0 12 12 0 001.28 6.61l4 3.09A7.15 7.15 0 0112 4.75z" />
    </svg>
  );
}
