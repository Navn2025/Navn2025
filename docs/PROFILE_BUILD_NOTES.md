# Profile content and portrait sources

Current source: `profile/source-photo-soft-background.png` retains the beige wall
with a light background-only blur. It was edited using built-in imagegen with
the full prompt saved in `profile/background-blur-prompt.txt`. The original
`profile/source-photo.png` is unchanged. The ASCII backdrop is now deliberately
styled as near-black with sparse faint punctuation, matching the supplied ASCII
reference. The existing cutout's alpha is used only as a silhouette sampling
guide; its RGB/person pixels are not used. Foreground pixels come from the
original/soft-background source. The editor opens the full softly blurred photo.
The complete source image and sampling matte are contained, rather than cover-
cropped, with 12% padding on all sides. Soft boundary cells are retained so the
body outline is not aggressively eroded. The dotted backdrop fills the padding.

The summary, education, experience and focused stack were checked against both
user-supplied resumes: `Navneet-Tripathi-Software-Engineer-Resume.pdf` and
`Navneet Tripathi-AI-Backend-Engineer.pdf`. The resumes are not included in the
public profile bundle. The two versions report different hackathon counts, so
no hackathon count is stated. LinkedIn and LeetCode links come from their embedded
PDF hyperlinks. The public profile omits the phone number.

The original supplied photograph remains in `profile/source-photo.png`.
The background-extracted copy is saved separately as `profile/portrait-cutout.png`.
It was created using the **built-in imagegen tool**, with actual transparent alpha.

Final image-edit prompt:

> Use case: background-extraction. Edit target: the supplied photograph of Navneet,
> a smiling young man wearing a blue kurta with folded arms. Remove ONLY the beige
> wall background. Produce a clean photographic foreground cutout on genuine
> transparent alpha. Preserve the exact person, face, hair, facial features, skin
> texture, expression, clothing, pose and visible hands of the original. No face
> re-generation, no beautification, no stylization, no relighting, no text, no extra
> objects. Keep his complete visible hair, ears, neck, shoulders, torso and arms.
> Keep the original framing; do not crop his body further. Leave a small transparent
> margin above and on both sides so his outline is clearly separated from the canvas.
> This cutout will be sampled into ASCII, so clean transparent edges around the hair,
> shoulders and sleeves matter.

The SVG generator contains the complete cutout within a padded square, erodes
the soft alpha edge before sampling, and only prints cells with at least 235/255
foreground coverage. Each glyph receives its own explicit horizontal coordinate,
and an outer clip contains the whole portrait. This fixes the earlier shoulder
crop and spacing drift caused by row-wide textLength with colored text runs.

The software stack uses 18 real Devicon marks. A dedicated AI section uses 10
real Simple Icons brand marks: LangChain, LangGraph, MCP, Hugging Face, Ollama,
Gemini, scikit-learn, NumPy, Pandas and OpenCV. There are no custom LC/LG/AWS
monograms. Sources and licenses are vendored in profile/icons.

The reference-matched portrait uses 100 columns and 78 rows, a detailed ramp of
letters and symbols, and regular-weight glyphs with visible gaps. Standalone
portraits are full-bleed artwork at 1000x1020, with no terminal frame or labels.
At native display size the characters are 13.5px tall, on a 10px horizontal and
13.05px vertical pitch. A very faint punctuation texture matches the reference's
black backdrop; it is deliberate texture, not remaining wall/background pixels.
The real cutout alpha still determines every foreground glyph. The homepage
shows the artwork at up to 896px wide, with the technical card underneath.
It samples from a 1024px working canvas and retains over 150 distinct grayscale
ink values, rather than the earlier eight-level mapping. Facial details are
sampled at high resolution before glyph placement. This corrects the horizontal
bands and loss of likeness in the earlier render. A standalone static portrait
is also included as `public/profile/portrait-static.svg`.
Its technical panel explicitly states B.Tech in Information Technology and
includes agents, RAG, evaluation, vision, security, real-time protocols and infra.
Versioned static asset URLs prevent an older portrait/panel from lingering.

The activity plot uses a trailing three-week average. Its display cap is the
90th percentile of those averages, rounded up to ten, with a configurable floor
of 20 and ceiling of 200. Amber points indicate clipped display values. Each
tooltip retains the true weekly count, average and clipping notice. Raw data,
total contributions, streaks and the contribution calendar are unchanged.
