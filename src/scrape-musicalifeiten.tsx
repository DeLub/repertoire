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
  const backendUrl = preferences.backendUrl || "http://localhost:5173";

  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>("");

  // Fetch a random page from musicalifeiten.nl
  const { data: htmlData, isLoading: isFetching, error: fetchError } = useFetch(
    "https://www.musicalifeiten.nl/composers/by-name/a/",
    {
      method: "GET",
      headers: {
        "User-Agent": "Repertoire/0.1.0 (Classical Music Manager)",
      },
    }
  );

  // Use Raycast AI to parse and enrich the fetched content
  const { data: aiResponse, isLoading: isAiProcessing, error: aiError } = useAI(
    `Extract classical music recording information from the following HTML content. 
    Return ONLY a valid JSON array with objects containing these fields: composer, work, performers (as array of strings), label, catalogNumber, releaseYear (as number), and notes.
    If no recordings are found, return an empty array [].
    Do NOT include markdown, code blocks, or any explanation.
    
    HTML Content:
    ${htmlData ? htmlData.substring(0, 3000) : "Loading..."}`
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
      setErrorMessage("");

      console.log("AI Response:", response);

      // Parse the AI response
      let parsedRecordings: Recording[] = [];
      
      try {
        // Try direct JSON parse first
        parsedRecordings = JSON.parse(response);
      } catch (parseError) {
        // If JSON parsing fails, try to extract JSON from the response
        console.log("Direct parse failed, trying regex extraction");
        const jsonMatch = response.match(/\[[\s\S]*\]/);
        if (jsonMatch) {
          console.log("Found JSON with regex:", jsonMatch[0]);
          parsedRecordings = JSON.parse(jsonMatch[0]);
        } else {
          throw new Error(`Could not parse AI response as JSON. Raw response: ${response.substring(0, 200)}`);
        }
      }

      if (!Array.isArray(parsedRecordings)) {
        parsedRecordings = [parsedRecordings];
      }

      console.log("Parsed recordings:", parsedRecordings);

      if (parsedRecordings.length === 0) {
        setErrorMessage("AI did not extract any recordings from the page. This might mean:\n\n- The page structure changed\n- The content is not about classical music\n- Try running again for a different page");
        await showToast({
          style: Toast.Style.Failure,
          title: "No recordings extracted",
          message: "The AI couldn't find any classical music recordings on this page",
        });
        return;
      }

      setRecordings(parsedRecordings);

      // Send to backend
      console.log("Sending to backend:", backendUrl);
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
        const errorText = await response_data.text();
        throw new Error(`Backend error (${response_data.status}): ${errorText}`);
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
      const errorMsg = error instanceof Error ? error.message : "Unknown error occurred";
      console.error("Error in processAIResponse:", errorMsg);
      setErrorMessage(errorMsg);
      
      await showToast({
        style: Toast.Style.Failure,
        title: "Error",
        message: errorMsg.substring(0, 100),
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const isLoading = isFetching || isAiProcessing || isProcessing;

  let markdown = "";

  if (fetchError) {
    markdown = `## Fetch Error\n\nFailed to fetch from musicalifeiten.nl:\n\n\`\`\`\n${fetchError.message}\n\`\`\`\n\nMake sure you have internet connection and the website is accessible.`;
  } else if (aiError) {
    markdown = `## AI Processing Error\n\nRaycast AI encountered an error:\n\n\`\`\`\n${aiError.message}\n\`\`\`\n\nPlease try again.`;
  } else if (isFetching) {
    markdown = "## Fetching page from musicalifeiten.nl...\n\nPlease wait...";
  } else if (isAiProcessing) {
    markdown = "## Processing with Raycast AI...\n\nExtracting composer, work, and performer information...\n\n*(This uses Raycast's built-in AI - make sure you have AI features enabled in Raycast)*";
  } else if (isProcessing) {
    markdown = "## Saving to database...\n\nConnecting to backend at " + backendUrl + "...\n\nMake sure the backend is running with `python -m repertoire.cli server`";
  } else if (errorMessage) {
    markdown = `## Error Details\n\n${errorMessage}`;
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
    markdown = `## Troubleshooting\n\n**No recordings were extracted.**\n\nPossible issues:\n\n1. **Raycast AI not configured** - Make sure Raycast AI is enabled in Raycast preferences\n2. **Page content issue** - The fetched page might not contain classical music metadata\n3. **AI parsing issue** - Try running again for a different page\n4. **Network issue** - Check your internet connection\n\n---\n\n**Debug Info:**\n- Backend URL: ${backendUrl}\n- HTML fetched: ${htmlData ? "Yes (" + htmlData.length + " bytes)" : "No"}\n- AI response: ${aiResponse ? "Received" : "Waiting..."}\n\n**Troubleshooting:**\n\n1. Check browser console (View → Toggle Developer Tools) for errors\n2. Make sure backend is running: \`python -m repertoire.cli server --port 5173\`\n3. Check Raycast logs: Search "Develop Extension" → Select Repertoire`;
  }

  return <Detail isLoading={isLoading} markdown={markdown} />;
}