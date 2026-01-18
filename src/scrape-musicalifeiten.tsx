import { Detail, showToast, Toast, open, getPreferenceValues } from "@raycast/api";
import { useAI, useFetch } from "@raycast/utils";
import { useEffect, useState } from "react";

interface Preferences {
  backendUrl: string;
}

interface Recording {
  composer: string;
  work: string;
  performers: string[];
  label?: string;
  catalogNumber?: string;
  releaseYear?: number;
  notes?: string;
}

export default function Command() {
  const preferences = getPreferenceValues<Preferences>();
  const backendUrl = preferences.backendUrl || "http://localhost:5000";

  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Fetch a random page from musicalifeiten.nl
  const { data: htmlData, isLoading: isFetching } = useFetch(
    "https://www.musicalifeiten.nl/composers/by-name/a/",
    {
      method: "GET",
      headers: {
        "User-Agent": "Repertoire/0.1.0 (Classical Music Manager)",
      },
    }
  );

  // Use Raycast AI to parse and enrich the fetched content
  const { data: aiResponse, isLoading: isAiProcessing } = useAI(
    `Extract classical music recording information from the following HTML content. 
    Return a JSON array with objects containing: composer, work, performers (array), label, catalogNumber, releaseYear, and notes.
    Only return valid JSON, no markdown or explanation.
    
    HTML Content:
    ${htmlData ? htmlData.substring(0, 2000) : "Loading..."}`
  );

  // Process AI response and save to backend
  useEffect(() => {
    if (!isAiProcessing && aiResponse) {
      processAIResponse(aiResponse);
    }
  }, [aiResponse, isAiProcessing]);

  const processAIResponse = async (response: string) => {
    try {
      setIsProcessing(true);

      // Parse the AI response
      let parsedRecordings: Recording[] = [];
      try {
        parsedRecordings = JSON.parse(response);
      } catch {
        // If JSON parsing fails, try to extract JSON from the response
        const jsonMatch = response.match(/\[[\s\S]*\]/);
        if (jsonMatch) {
          parsedRecordings = JSON.parse(jsonMatch[0]);
        } else {
          throw new Error("Could not parse AI response as JSON");
        }
      }

      if (!Array.isArray(parsedRecordings)) {
        parsedRecordings = [parsedRecordings];
      }

      setRecordings(parsedRecordings);

      // Send to backend
      const response_data = await fetch(`${backendUrl}/api/recordings`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          recordings: parsedRecordings,
        }),
      });

      if (!response_data.ok) {
        throw new Error(`Backend error: ${response_data.statusText}`);
      }

      await showToast({
        style: Toast.Style.Success,
        title: "Success!",
        message: `Saved ${parsedRecordings.length} recording(s) to database`,
      });

      // Optionally open the web UI
      setTimeout(() => {
        open(`${backendUrl}`);
      }, 1000);
    } catch (error) {
      await showToast({
        style: Toast.Style.Failure,
        title: "Error",
        message: error instanceof Error ? error.message : "Unknown error occurred",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const isLoading = isFetching || isAiProcessing || isProcessing;

  let markdown = "";

  if (isFetching) {
    markdown = "## Fetching page from musicalifeiten.nl...\n\nPlease wait...";
  } else if (isAiProcessing) {
    markdown = "## Processing with Raycast AI...\n\nExtracting composer, work, and performer information...";
  } else if (isProcessing) {
    markdown = "## Saving to database...\n\nConnecting to backend...";
  } else if (recordings.length > 0) {
    markdown = "## Recordings Extracted\n\n";
    markdown += `Found **${recordings.length}** recording(s):\n\n`;

    recordings.forEach((rec, index) => {
      markdown += `### ${index + 1}. ${rec.work}\n`;
      markdown += `**Composer:** ${rec.composer}\n\n`;
      if (rec.performers?.length > 0) {
        markdown += `**Performers:** ${rec.performers.join(", ")}\n\n`;
      }
      if (rec.label) {
        markdown += `**Label:** ${rec.label}\n\n`;
      }
      if (rec.catalogNumber) {
        markdown += `**Catalog:** ${rec.catalogNumber}\n\n`;
      }
      if (rec.releaseYear) {
        markdown += `**Year:** ${rec.releaseYear}\n\n`;
      }
      if (rec.notes) {
        markdown += `**Notes:** ${rec.notes}\n\n`;
      }
    });

    markdown += "\n---\n\n✅ Data saved to database! The web UI will open shortly...";
  } else {
    markdown = "## Error\n\nNo recordings were extracted. Please try again.";
  }

  return <Detail isLoading={isLoading} markdown={markdown} />;
}