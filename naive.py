def naive_search(text, pattern):
    """Find all occurrences of the pattern in the text using the Naïve approach with i, j, k."""
    n, m = len(text), len(pattern)
    result = []

    for i in range(n - m + 1): 
        x = 0
        while x < m and text[x+i] == pattern[x]: 
            x += 1
        if x == m:
            result.append(i)

    if result:
        print("Pattern found at indices:", result)
    else:
        print("Pattern not found")

    return result



text = "ababcababcabc"
pattern = "abc"  
naive_search(text, pattern)
