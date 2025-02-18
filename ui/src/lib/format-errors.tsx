import { Badge, badgeVariants } from "@/components/ui/badge";
import { processTestOutput } from "./process-test-output";
import Link from "next/link";

interface ITest {
  status: string;
  name: string;
  duration: number;
  message?: string;
}

export function FormatErrors({ inputString }: { inputString?: string }) {
  if (!inputString) return "";
  // Detect and remove the dynamic path
  const cleanedString = inputString
    .replace(/\/tmp\/playground\/[a-f0-9\-]+\//g, "")
    .replace(/\/tmp\/[a-f0-9\-]+/g, "");

  // Regular expression to match lines containing errors and warnings
  const errorMessages = cleanedString.match(
    /(\w+\/[^\n]*): (error|warning) [^\n]*/g
  );

  const testResults = processTestOutput(inputString);

  return (
    <>
      {errorMessages ? (
        <table>
          <thead>
            <tr>
              <th className="p-2">Path</th>
              <th className="p-2">Type</th>
              <th className="p-2">Description</th>
            </tr>
          </thead>
          {errorMessages.map((m) => (
            <ErrorMessage key={m} message={m} />
          ))}
        </table>
      ) : null}
      {testResults.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th className="p-2">Status</th>
              <th className="p-2">Name</th>
              <th className="p-2">Duration (ms)</th>
            </tr>
          </thead>
          {testResults.map((test: ITest, key: number) => (
            <TestResult key={`${test.name}-${key}`} test={test} />
          ))}
        </table>
      ) : null}

      {!errorMessages && !(testResults.length > 0) && inputString}
    </>
  );
}

function TestResult({ test }: { test: ITest }) {
  return (
    <tr className="border border-black">
      <td className="p-2">
        <Badge variant={test.status === "passed" ? "default" : "destructive"}>
          {test.status}
        </Badge>
      </td>
      <td className="p-2">
        {test.name}
        <br />
        {test?.message}
      </td>
      <td className="p-2">{test.duration}</td>
    </tr>
  );
}

function ErrorMessage({ message }: { message: string }) {
  const [path, type, ...description] = message.split(":").map((i) => i.trim());

  return (
    <tr className="border border-black">
      <td className="p-2">{path}</td>
      <td className="p-2">
        <ErrorTypeLink type={type} />
      </td>
      <td className="p-2">{description.join(" ")}</td>
    </tr>
  );
}

function ErrorTypeLink({ type }: { type: string }) {
  const [kind, code] = type.split(" ");

  if (kind === "warning") return <Badge variant="secondary">warning</Badge>;

  if (kind === "error" && code?.startsWith("CS"))
    return (
      <Link
        className={badgeVariants({
          variant: "destructive",
        })}
        href={`https://learn.microsoft.com/en-us/dotnet/csharp/misc/${code.toLowerCase()}`}
        target="_blank"
        rel="noopener noreferrer"
      >
        <span className="text-white">{code}</span>
      </Link>
    );

  return null;
}
