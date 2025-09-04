#!/bin/bash
# fetch-archive-range.sh
# Usage: ./fetch-archive-range.sh PROJECT START_DATE END_DATE

project="$1"
start="$2"
end="$3"

if [ -z "$project" ] || [ -z "$start" ] || [ -z "$end" ]; then
  echo "Usage: $0 PROJECT START_DATE END_DATE"
  echo "Example: $0 my-project 2024-01-01 2024-03-31"
  exit 1
fi

start_epoch=$(date -d "$start" +%s) || { echo "Invalid START_DATE: $start"; exit 1; }
end_epoch=$(date -d "$end" +%s)     || { echo "Invalid END_DATE: $end"; exit 1; }

if [ "$start_epoch" -gt "$end_epoch" ]; then
  echo "Error: START_DATE ($start) is later than END_DATE ($end)"
  exit 1
fi

failed=()
succeeded=0
total=0

print_summary() {
  echo
  echo "Summary:"
  echo "  Total dates: $total"
  echo "  Succeeded:   $succeeded"
  echo "  Failed:      ${#failed[@]}"
  if [ "${#failed[@]}" -gt 0 ]; then
    printf "  Failed dates: %s\n" "${failed[@]}"
  fi
}

trap print_summary EXIT

d="$start"
end_plus_one="$(date -I -d "$end + 1 day")"

while [ "$d" != "$end_plus_one" ]; do
  total=$((total+1))
  echo "Fetching $d for project $project"
  if uv run lse archive fetch --project "$project" --date "$d" --include-children; then
    succeeded=$((succeeded+1))
  else
    echo "Warning: fetch failed for $d" >&2
    failed+=("$d")
  fi
  d=$(date -I -d "$d + 1 day")
done

# Set exit code after summary prints via trap
[ "${#failed[@]}" -eq 0 ]
