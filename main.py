from semantica import Semantica

s = Semantica('./models/GoogleNews-vectors-negative300.bin', word_count=80000)

samples = []

samples += [s.field("tree")]
samples += [s.mix("breakfast", "lunch", "dinner")]
samples += [s.mix("king", shift=["man", "woman"])]
samples += [s.mix("burrito", shift=["Spain", "Italy"])]
#samples += [s.span("car", "boat")]
samples += [s.model("king", "queen")]

for i in range(len(samples)):
    print('Sample', str(i))
    print(*samples[i])
    print()