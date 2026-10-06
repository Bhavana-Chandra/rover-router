# Demo video script (90 to 120 seconds)

Numbers below come from `results/summary.txt` (20 seeds each) and from
`python demo.py` on seed 16. If you re-run the benchmark, check them again.

## Timeline

| Time | On screen | What I say |
|---|---|---|
| 0:00 - 0:15 | Title slide, then the Water_Rover repo page | "Last year our team built a rover that collects floating debris from water. A person steers it by hand. If debris is scattered across a lake, the order of visits decides how much battery the rover uses." |
| 0:15 - 0:30 | Slide: "Why quantum" | "Finding the shortest route through all the spots is the travelling salesman problem. It gets hard fast as spots are added. QAOA is a quantum algorithm that researchers are testing on problems like this. I am not claiming it is faster. I wanted to see what it does on a tiny lake." |
| 0:30 - 1:20 | Terminal: `python demo.py`, then the route figure | "This is a simulated five by five lake with a dock and four debris spots. First it builds the problem as a QUBO. That is sixteen variables, so sixteen qubits. Then QAOA runs on a simulator. It takes a few seconds. Now the comparison. The exact answer is length 14. Greedy gets 16. QAOA also gets 16, with the same route as greedy. On the map, green is exact, orange is greedy, purple is QAOA." |
| 1:20 - 1:35 | `results/benchmark.png` | "Over twenty random lakes, greedy was within 3 percent of optimal on average. QAOA at depth one was 13 percent off and found no valid route at all on 5 lakes. Random sampling with the same number of shots did worse than QAOA, so QAOA is doing something, but greedy was better." |
| 1:35 - 1:45 | Slide: "Limits and next steps" | "Everything here is a simulation: tiny grid, four spots, no hardware. Next I want to try real IBM hardware, add a noise study, and eventually send waypoints to the real rover." |

Total is about 105 seconds spoken. Trim the benchmark line if it runs long.

## Before recording

- Run `python demo.py` once live so `results/demo_cached.json` is fresh.
- For retakes use `python demo.py --cached`. It prints that the QAOA result is
  cached, so say "this is the saved result from my earlier run" if you use it
  in the final video.
- Make the terminal font large (about 20 pt) so it reads on a phone.

## Recording steps

1. Do a dry run of `demo.py`. Close other windows and turn off notifications.
2. Screen-record the terminal and the plot with OBS Studio or the built-in
   recorder at 1080p, no voice. Do 2 or 3 clean takes.
3. Record the voiceover separately while watching a clean take, in a quiet room
   with a decent mic. Check the hackathon FAQ on AI-generated voiceovers before
   using any AI voice tool. [FILL: confirm the policy.]
4. Join clips in CapCut or Clipchamp, add a title card with your name, export MP4.
5. Upload as an unlisted YouTube video or a Drive link with sharing on. Open the
   link in a private window to test it before submitting.
