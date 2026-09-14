---
title: "Five languages, one patient"
date: 2027-02-11
status: approved
tag: healthcare
summary: "Clinical documents arrive in whatever language the patient's last doctor spoke. The system has to be honest about what it can read."
linkedin_url:
---

Clinical documents arrive in whatever language the patient's last doctor happened to speak.

In the EMR I architected, that meant intake in five languages on a normal week. Scanned referrals. Handwritten notes. Lab results formatted three different ways. Sometimes the same patient under three spellings of their name.

The tempting design is to run all of it through OCR and a model and produce a clean, unified record. It would work most of the time. In healthcare, "most of the time" is a liability.

So the system was designed to be honest about its own confidence.

Extraction produced a candidate, never a fact. Every field carried a confidence score and a pointer to the exact region of the source it came from.
Anything below threshold went to a human queue, in the original language, with the candidate shown alongside. Not hidden, not auto-accepted.
Name matching proposed, it never merged. A human confirmed that two records were one person, and that decision was logged with who made it.
The source document stayed immutable, forever, next to everything derived from it.

The machine did the reading. People did the deciding. The architecture made sure nobody could confuse the two.

Where in your system does a guess get treated as a fact?
