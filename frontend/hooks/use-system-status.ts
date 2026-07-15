"use client";

import { useCallback, useEffect, useState } from "react";
import { getHealth, getSystemInfo } from "@/lib/api";
import type { ConnectivityState, SystemInfoResponse } from "@/types/api";

export function useSystemStatus() {
  const [state, setState] = useState<ConnectivityState>("checking");
  const [system, setSystem] = useState<SystemInfoResponse | null>(null);
  const check = useCallback(async () => {
    setState("checking");
    try {
      const [, info] = await Promise.all([getHealth(), getSystemInfo()]);
      setSystem(info);
      setState("connected");
    } catch {
      setSystem(null);
      setState("unavailable");
    }
  }, []);
  useEffect(() => {
    let active = true;
    void Promise.all([getHealth(), getSystemInfo()])
      .then(([, info]) => {
        if (active) {
          setSystem(info);
          setState("connected");
        }
      })
      .catch(() => {
        if (active) setState("unavailable");
      });
    return () => {
      active = false;
    };
  }, []);
  return { state, system, retry: check };
}
