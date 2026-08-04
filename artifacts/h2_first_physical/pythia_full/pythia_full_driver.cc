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
  if (argc != 7) {
    std::cerr << "usage: pythia_llp_full events.lhe[.gz] decay.slha point.json metrics.csv summary.json seed\n";
    return 2;
  }
  const std::string lhe = argv[1], slha = argv[2], pointPath = argv[3];
  const std::string seed = argv[6];
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
  const int maxEvents = 10000;
  while (nEvents < maxEvents && pythia.next()) {
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
  pythia.stat();
  std::ofstream js(argv[5]);
  js << std::setprecision(16);
  js << "{\n"
     << "  \"events\": " << nEvents << ",\n"
     << "  \"llp_records\": " << nLLP << ",\n"
     << "  \"production_h2_records_from_lhe\": " << 2 * nEvents << ",\n"
     << "  \"llp_decayed\": " << nDecayed << ",\n"
     << "  \"b_quarks_from_h2\": " << nB << ",\n"
     << "  \"tau0_configured_mm\": " << pythia.particleData.tau0(9000006) << ",\n"
     << "  \"mean_tau_generated_mm\": " << (nLLP ? sumTau/nLLP : 0.0) << ",\n"
     << "  \"mean_L3D_mm\": " << (nLLP ? sumL3D/nLLP : 0.0) << ",\n"
     << "  \"mean_Rxy_mm\": " << (nLLP ? sumRxy/nLLP : 0.0) << ",\n"
     << "  \"fraction_Rxy_gt_4mm\": " << (nLLP ? double(nRxy4)/nLLP : 0.0) << "\n"
     << "}\n";
  return (nEvents > 0 && nB == 4 * nEvents) ? 0 : 4;
}
