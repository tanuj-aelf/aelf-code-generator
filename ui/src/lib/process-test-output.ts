export function processTestOutput(str: string) {

  const results = [];
  const lines = str.split('\n');

  let lineNum = 0;

  for (const line of lines) {

    const status = line.match(/^\s*(Passed|Failed)\s+/)?.[1].toLowerCase();

    if (status) {
      const match = line.match(/^\s*(Passed|Failed)\s+(.+?)\s+\[(\d+(\.\d+)?\s*s|(\d+)\s*ms)\]$/);

      const name = match?.[2] || '';

      const durationStr = match?.[3];
      let duration = 0;

      if (durationStr?.endsWith('ms')) {
        duration = parseInt(durationStr.split(' ms')[0]);
      } else if (durationStr?.endsWith('s')) {
        duration = parseFloat(durationStr.split(' s')[0]) * 1000;
      }

      let message: string | undefined;

      if (status === 'failed') {
        // Find the error message. It is between the next line and "Stack Trace:"
        
        const start = lineNum + 2;
        const end = lines.slice(start).findIndex(l => l.includes('Stack Trace:')) + start;
        message = lines.slice(start, end).map(i => i.trim()).join(' ');

        console.log(message);
      }

      results.push({name, status, duration, message});
    }

    lineNum++;
  }

  return results;
}