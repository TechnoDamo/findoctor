import { appConfig } from "@/lib/config";

function normalizePath(path: string): string {
  if (path.startsWith("/")) {
    return path;
  }

  return `/${path}`;
}

export function buildBackendUrl(path: string): string {
  return `${appConfig.backend.baseUrl}${normalizePath(path)}`;
}
