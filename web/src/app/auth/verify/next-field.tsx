"use client";

import { useEffect, useState } from "react";

/** Carries the page the builder wanted before signing in (saved on the login page). */
export function NextField() {
  const [next, setNext] = useState("");
  useEffect(() => {
    setNext(sessionStorage.getItem("onefold-next") ?? "");
  }, []);
  return <input type="hidden" name="next" value={next} />;
}
