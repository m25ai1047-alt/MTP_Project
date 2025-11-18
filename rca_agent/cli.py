import sys
import json
from rca_service import perform_root_cause_analysis

def main():
    if len(sys.argv) < 2:
        print("Usage: python cli.py '<error_log_message>'")
        print("\nExample:")
        print("  python cli.py 'java.lang.NullPointerException at com.example.UserService.getUser(UserService.java:42)'")
        sys.exit(1)

    error_log = sys.argv[1]

    print("Analyzing error log...")
    print("-" * 80)

    result = perform_root_cause_analysis(error_log)

    print("\n=== ROOT CAUSE ANALYSIS ===\n")
    print(f"Error: {result['error_log']}\n")
    print(f"Analysis:\n{result['analysis']}\n")

    if result['relevant_code']:
        print(f"\nFound {len(result['relevant_code'])} relevant code snippet(s)")
        for i, code in enumerate(result['relevant_code'], 1):
            metadata = code.get('metadata', {})
            print(f"\n{i}. {metadata.get('file_path', 'Unknown')} - {metadata.get('method_name', 'Unknown')}")

    if result['keywords_extracted']:
        print(f"\nKeywords: {', '.join(result['keywords_extracted'])}")

    # Save detailed results to file
    with open('rca_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("\nDetailed results saved to rca_result.json")

if __name__ == "__main__":
    main()
