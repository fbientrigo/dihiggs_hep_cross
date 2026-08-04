#include "Pythia8/Pythia.h"
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace Pythia8;

static double jsonNumber(const std::string& text, const std::string& key) {
  const std::string needle = "\"" + key + "\"";
  auto pos = text.find(needle);
  if (pos == std::string::npos) throw std::runtime_error("Missing JSON key " + key);
  pos = text.find(':', pos + needle.size());
  if (pos == std::string::npos) throw std::runtime_error("Malformed JSON key " + key);
  return std::stod(text.substr(pos + 1));
}

int main(int argc, char** argv) {
  if (argc != 8) {
    std::cerr << "usage: pythia_llp_full events.lhe[.gz] decay.slha point.json "
                  "metrics.csv summary.json seed expected_events\n";
    return 2;
  }
  const std::string lhe = argv[1], slha = argv[2], pointPath = argv[3];
  const std::string seed = argv[6];
  const long long expectedEvents = std::stoll(argv[7]);
  if (expectedEvents <= 0) {
    std::cerr << "expected_events must be a positive integer\n";
    return 2;
  }
  std::ifstream pin(pointPath);
  std::stringstream pbuf; pbuf << pin.rdbuf();
  const double ctauMm = jsonNumber(pbuf.str(), "ctau_mm");

  Pythia pythia;
  pythia.readString("Beams:frameType = 4");
  pythia.readString("Beams:LHEF = " + lhe);
  pythia.readString("SLHA:readFrom = 2");
  pythia.readString("SLHA:file = " + slha);
  pythia.readString("SLHA:useDecayTable = on");
  pythia.readString("SLHA:allowUserOverride = on");
  pythia.readString("Random:setSeed = on");
  pythia.readString("Random:seed = " + seed);
  pythia.readString("LesHouches:setLifetime = 2");
  pythia.readString("ParticleDecays:limitTau0 = off");
  pythia.readString("PartonLevel:ISR = off");
  pythia.readString("PartonLevel:FSR = off");
  pythia.readString("PartonLevel:MPI = off");
  pythia.readString("BeamRemnants:primordialKT = off");
  pythia.readString("HadronLevel:Decay = on");
  pythia.readString("Next:numberShowEvent = 0");
  pythia.readString("Next:numberShowInfo = 0");
  pythia.readString("Next:numberShowProcess = 0");
  pythia.readString("HadronLevel:Hadronize = on");
  if (!pythia.init()) return 3;
  pythia.particleData.mayDecay(9000006, true);
  pythia.particleData.tau0(9000006, ctauMm);

  std::ofstream csv(argv[4]);
  csv << "event,index,tau0_mm,tau_generated_mm,L3D_mm,Rxy_mm,n_daughters\n";
  long long nEvents = 0, nLLP = 0, nProductionLLP = 0, nRxy4 = 0, nDecayed = 0, nB = 0;
  double sumTau = 0.0, sumL3D = 0.0, sumRxy = 0.0;
  while (nEvents < expectedEvents) {
    if (!pythia.next()) {
      // next() failing before the expected count is reached is always an
      // error: EOF this early means the LHE is short of expected_events
      // (truncated input), and a non-EOF failure is a recoverable/fatal
      // generation error. Neither may be reported as a completed sample.
      if (pythia.info.atEndOfFile()) {
        std::cerr << "truncated LHE input: EOF after " << nEvents
                   << " of " << expectedEvents << " expected events\n";
        return 4;
      }
      std::cerr << "Pythia event generation failed before reaching "
                 << expectedEvents << " expected events (at event "
                 << nEvents << ")\n";
      return 5;
    }
    ++nEvents;
    for (int i = 0; i < pythia.event.size(); ++i) {
      const Particle& p = pythia.event[i];
      if (std::abs(p.id()) != 9000006) continue;
      // Pythia keeps intermediate H2 copies in the event record; only the
      // terminal forced bb record is one physical decay per LLP.
      if (p.daughterList().size() != 2) continue;
      ++nLLP;
      if (p.mother1() == 1 && p.mother2() == 2) ++nProductionLLP;
      const double dx = p.xDec() - p.xProd();
      const double dy = p.yDec() - p.yProd();
      const double dz = p.zDec() - p.zProd();
      const double rxy = std::hypot(dx, dy);
      const double l3d = std::sqrt(dx*dx + dy*dy + dz*dz);
      const int nd = p.daughterList().size();
      if (nd > 0) ++nDecayed;
      for (int daughter : p.daughterList()) {
        if (std::abs(pythia.event[daughter].id()) == 5) ++nB;
      }
      if (rxy > 4.0) ++nRxy4;
      sumTau += p.tau(); sumL3D += l3d; sumRxy += rxy;
      csv << nEvents << ',' << i << ',' << std::setprecision(16)
          << pythia.particleData.tau0(9000006) << ',' << p.tau() << ','
          << l3d << ',' << rxy << ',' << nd << '\n';
    }
  }
  // The loop above stops exactly at expected_events regardless of how much
  // input remains. Probe one more event to confirm the LHE did not contain
  // more than expected_events: a successful read, or a failure that is not
  // clean EOF, means expected_events under-states the input and the sample
  // silently dropped trailing events.
  const bool extraEventAvailable = pythia.next();
  if (extraEventAvailable) {
    std::cerr << "LHE input contains more than the expected " << expectedEvents
               << " events\n";
    return 6;
  }
  if (!pythia.info.atEndOfFile()) {
    std::cerr << "Pythia event generation failed while confirming end-of-file "
                  "after " << expectedEvents << " expected events\n";
    return 6;
  }
  pythia.stat();
  const bool countsOk = nEvents == expectedEvents &&
                         nLLP == 2 * expectedEvents &&
                         nDecayed == 2 * expectedEvents &&
                         nB == 4 * expectedEvents;
  std::ofstream js(argv[5]);
  js << std::setprecision(16);
  js << "{\n"
     << "  \"events\": " << nEvents << ",\n"
     << "  \"expected_events\": " << expectedEvents << ",\n"
     << "  \"llp_records\": " << nLLP << ",\n"
     << "  \"production_h2_records_from_lhe\": " << 2 * nEvents << ",\n"
     << "  \"llp_decayed\": " << nDecayed << ",\n"
     << "  \"b_quarks_from_h2\": " << nB << ",\n"
     << "  \"tau0_configured_mm\": " << pythia.particleData.tau0(9000006) << ",\n"
     << "  \"mean_tau_generated_mm\": " << (nLLP ? sumTau/nLLP : 0.0) << ",\n"
     << "  \"mean_L3D_mm\": " << (nLLP ? sumL3D/nLLP : 0.0) << ",\n"
     << "  \"mean_Rxy_mm\": " << (nLLP ? sumRxy/nLLP : 0.0) << ",\n"
     << "  \"fraction_Rxy_gt_4mm\": " << (nLLP ? double(nRxy4)/nLLP : 0.0) << ",\n"
     << "  \"status\": \"" << (countsOk ? "PASS" : "FAIL") << "\"\n"
     << "}\n";
  if (!countsOk) {
    std::cerr << "event/LLP/decay/b-quark counts do not match expected_events="
               << expectedEvents << " (events=" << nEvents << " llp=" << nLLP
               << " decayed=" << nDecayed << " b=" << nB << ")\n";
    return 7;
  }
  return 0;
}
