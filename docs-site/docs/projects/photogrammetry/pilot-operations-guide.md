# Pilot Operations Guide: Task 1.2 — Coral Garden Ridge Modelling

> **Competition:** MATE 2026 Explorer — Task 1.2
> **Option A (Photogrammetry):** up to 40 points
> **Option B (Manual CAD):** up to 30 points
> **You can attempt BOTH and take whichever scores higher.**

---

## Scoring Breakdown

### Option A: Autonomous Photogrammetry (up to 40 pts)

| Step | What you do | Points | Judge interaction |
|------|------------|--------|-------------------|
| **A1. 3D Model** | Generate a photogrammetry model showing the colored target squares | 5-20 pts (see below) | Judge rotates the model on screen |
| **A2. Measure Length** | Physically measure the coral garden length with the ROV | 10 pts (within 5 cm) | Show judge your method — no guessing allowed |
| **A3. Scale Model** | Enter the true length into the system, display it on the 3D model | 5 pts | Judge sees the true length displayed on the model |
| **A4. Estimate Height** | Use the scaled model to digitally estimate the height | 5 pts (within 5 cm) | Judge sees the height displayed on the model |

**3D Model quality scoring (Step A1):**

| Targets visible in model | Points |
|--------------------------|--------|
| All 8 colored squares | 20 |
| 4 to 7 squares | 15 |
| 1 to 3 squares | 10 |
| 0 targets (but model exists) | 5 |

### Option B: Manual CAD (up to 30 pts)

| Step | What you do | Points | Judge interaction |
|------|------------|--------|-------------------|
| **B1. Measure Length** | Physically measure with ROV | 10 pts (within 5 cm) | Show judge your method |
| **B2. Measure Height** | Physically measure with ROV | 10 pts (within 5 cm) | Show judge your method |
| **B3. Create 3D Model** | Input both measurements into CAD, generate model with dimensions shown | 10 pts | Judge sees three rectangular prisms with length + height labels |

---

## The Gated Flow

```
┌─────────────────────────────────────────────────────┐
│  STEP 1: Measure the length (both options need this) │
│                                                       │
│  Pilot measures length with ROV tools                │
│  → Tell judge your measurement + explain method       │
│  → Judge awards 0-10 points                          │
│  → Judge gives you the TRUE LENGTH                   │
│                                                       │
│  ⚠ If you don't attempt this, you get NO true length │
│    and cannot complete any remaining steps!           │
└───────────────────────┬─────────────────────────────┘
                        │
           ┌────────────┴────────────┐
           ▼                         ▼
   ┌───────────────┐       ┌─────────────────┐
   │  OPTION A      │       │  OPTION B        │
   │  Photogrammetry│       │  Manual CAD      │
   │                │       │                  │
   │  Enter true    │       │  Measure height  │
   │  length →      │       │  with ROV →      │
   │  scale model → │       │  enter both →    │
   │  get height    │       │  generate model  │
   │                │       │                  │
   │  Max: 40 pts   │       │  Max: 30 pts     │
   └───────────────┘       └─────────────────┘
```

---

## What You Know Before Starting

| Given | Value |
|-------|-------|
| Structure | 1/2-inch PVC pipe |
| Length | Between 1 m and 2.5 m (unknown exact value) |
| Width | Approximately 36 cm |
| Height | **Unknown** — this is what you must find |
| Visual targets | Eight 10 cm x 10 cm colored squares on the structure |
| Allowed tools | You may place a ruler or known-dimension object near the garden |

The **colored squares** (10 cm x 10 cm) serve two purposes:
1. **Scoring** — more visible targets in the model = more points (up to 20)
2. **Scale reference** — each is a known 10 cm measurement you can use for verification

---

## Competition Procedure

### Phase 0: Start Image Capture Immediately (Copilot)

The 3D model takes 5-10 minutes to generate. **Start this as soon as the ROV reaches the coral garden.** You don't need the true length yet — just photos.

1. On the **Co-Pilot page**, press the **red record button** on the camera aimed at the coral
2. **Pilot slowly around the entire coral garden:**
    - Maintain ~30-50 cm distance
    - Move slowly — no sudden turns or motion blur
    - **Orbit the full structure** from multiple angles around it
    - Capture from different heights (above, level, slightly below)
    - **Ensure all 8 colored squares** are clearly visible in at least several frames each — this is worth up to 20 points
    - Aim for **60-80% overlap** between successive viewpoints
    - 15-30 images minimum
3. Press **stop** — browser extracts frames and downloads a ZIP
4. Go to the **Photogrammetry page**, upload the folder, and click **"Generate Model"**
5. The pipeline runs in the background — proceed to Step 1 while it processes

### Step 1: Measure the Length (10 points) — REQUIRED FOR EVERYTHING ELSE

**You MUST attempt this. If you skip it, the judge will NOT give you the true length.**

**Methods:**

| Method | How | Notes |
|--------|-----|-------|
| **Laser pointers** | Known separation (e.g. 10 cm). Traverse the coral, count how many laser-widths fit. | Most common method |
| **Physical ruler** | Place alongside the coral using the manipulator arm | Must retrieve before demo ends (counts as debris otherwise) |
| **Colored squares** | Each is 10 cm x 10 cm. Count how many fit along the length. | Can verify from camera footage |
| **ROV/arm reference** | Use the manipulator arm or ROV body as a known-length reference | Must know the exact dimension |

**Procedure:**
1. Pilot measures the length using one of the methods above
2. Copilot records the number
3. **Tell the station judge:** "We measured the length as X cm. We measured it by [method]."
4. Judge awards up to **10 points** if within 5 cm
5. **The judge gives you the TRUE LENGTH** — write this down immediately

### Step 2A: Scale Model + Estimate Height (Option A — 10 more points)

Once you have the true length from the judge AND the 3D model has finished generating:

1. Enter the **true length** (from the judge) into the **"True Coral Length"** field
2. Click **"Estimate Height"**
3. The system:
    - Calculates scale factor: `S = true_length / model_longest_horizontal_extent`
    - Calculates height: `H = model_vertical_extent x S`
    - Displays both the **true length** and **estimated height** on the model
4. **Show the judge:**
    - The 3D model (rotatable) — judge checks target visibility (5-20 pts)
    - The **true length displayed on the model** — judge verifies (5 pts)
    - The **estimated height displayed on the model** — judge checks if within 5 cm (5 pts)

### Step 2B: Manual CAD Fallback (Option B — 20 more points)

Do this **in parallel** if time allows, or as a backup if the pipeline fails:

1. **Physically measure the height** using the same tools as length measurement
2. On the **Photogrammetry page:**
    - Enter the **true length** (from judge) in "True Coral Length"
    - Enter your **measured height** in "Estimated Coral Height"
3. Click **"Manual CAD Model"**
4. **Show the judge** the model with **three rectangular prisms** showing both dimensions

---

## Scaling Algorithm

```
Inputs:
  true_length:  Exact length given by the judge (cm)
  3D model:     The GLB mesh generated from your photos

Step 1: Compute bounding box of the 3D model
  L_model = longest horizontal extent (model units)
  H_model = vertical extent (model units)

Step 2: Scale Factor
  S = true_length / L_model

Step 3: Real Height
  H_real = H_model x S

Step 4: Display (judge must see both)
  "Length: [true_length] cm"
  "Height: [H_real] cm"
```

---

## Recommended Strategy

**Do both options simultaneously:**

| Time | Pilot | Copilot |
|------|-------|---------|
| 0:00 | Navigate to coral | — |
| 0:30 | Orbit coral (copilot records) | Start camera recording |
| 3:00 | Begin length measurement | Stop recording, upload images, click Generate |
| 5:00 | Begin height measurement | Pipeline running in background |
| 7:00 | Report length to judge → get TRUE LENGTH | Enter true length if model is ready |
| 8:00 | Report height to judge (Option B) | Click "Manual CAD Model" with both measurements |
| 9:00 | — | If pipeline done: click "Estimate Height" (Option A) |
| 10:00 | — | Show judge BOTH models, take higher score |

**Option B is the safe bet** (30 pts, guaranteed if measurements are good). **Option A is the bonus** (40 pts if the model is high quality with targets visible). Doing both maximizes your score.

---

## Timing Guide

| Phase | Time | Notes |
|-------|------|-------|
| Image capture + start pipeline | 3 min | Do FIRST |
| Length measurement | 2 min | While model generates |
| Height measurement (Option B) | 2 min | While model generates |
| Report to judge, get true length | 1 min | **Write down the true length!** |
| Enter true length + scale/estimate | 30 sec | After judge gives true length |
| Manual CAD model | 30 sec | Enter height + length, click button |
| Show judge results | 1-2 min | Show both models if you have them |
| **Total** | **~10-12 min** | Fits within 15-min demo window |

---

## Troubleshooting During Competition

| Problem | Quick fix |
|---------|-----------|
| Pipeline still running | Use Option B (Manual CAD) — instant, worth 30 pts |
| Model has few/no targets visible | Still worth 5 pts. Focus on Option B for more points. |
| Height estimate seems wrong | Check you entered the TRUE length (from judge), not your own estimate |
| Model not textured | Geometry still works for height estimation. Targets may not be visible though. |
| Backend not responding | Option B only needs the Manual CAD endpoint. Restart Docker if possible. |
| Judge won't give true length | You must attempt to measure length first. Show your method. |
| Object left in pool | Any ruler/reference object counts as debris if not retrieved! |

---

## Pre-Competition Checklist

- [ ] Docker Desktop running with 8GB+ RAM
- [ ] Photogrammetry backend container tested end-to-end
- [ ] Frontend connects to backend (`curl http://localhost:8100/api/health`)
- [ ] Camera recording tested (Co-Pilot page: record → stop → ZIP download works)
- [ ] Full pipeline test: upload images → generate → enter length → estimate height
- [ ] Manual CAD tested: enter length + height → generate → verify dimensions shown
- [ ] Laser pointers or reference tools calibrated and mounted on ROV
- [ ] Team knows the exact dimensions of the manipulator arm / ROV body for reference
- [ ] Practice the judge interaction: "We measured X cm by [method]"
- [ ] **Roles assigned:**
    - **Pilot:** Drives ROV, measures length and height with tools
    - **Copilot:** Records camera, operates UI, presents results to judge
