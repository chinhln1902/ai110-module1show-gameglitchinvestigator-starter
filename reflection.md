# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").
  + the hints feature doesn't work: It should be more precise
  + accept negative numbers: Should yell at user don't put negative numbers
  + New Game doesn't work: Should refresh attempt and notify user
  + Developer Debug Info display incorrectly: should display attempt, history correctly

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|-------------------|-----------------|------------------------|
|Input -1|Shows "negative numbers are not accepted|Still says "go lower/higher"|
|Press New game|Display "New game has been created"|Nothing happened|
|Press submit|The logs in developer tool should be updated immediately|Nothing happened till next hit|


---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
  + I used Claude
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
  + It suggested the
- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.
  + It suggested create new file to make project root importable for testing purpose. But I told it we wouldn't need it because I'll test it manually and in terminal.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
  + I used the table in Section 1 to test the bugs manually. And the test cases
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
  + I tested the negative number bug, it showed me the parse_guess method didn't handle that negative number.
- Did AI help you design or understand any tests? How?
  + Yes, it showed me quickly where the code failed and

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
