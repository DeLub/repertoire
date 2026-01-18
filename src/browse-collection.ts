import { open } from "@raycast/api";
import { getPreferenceValues } from "@raycast/api";

interface Preferences {
  backendUrl: string;
}

export default function Command() {
  const preferences = getPreferenceValues<Preferences>();
  const backendUrl = preferences.backendUrl || "http://localhost:5000";

  open(backendUrl);
}
