import {
  AlertTriangle,
  Check,
  Copy,
  ShieldCheck,
  Terminal,
} from 'lucide-react'

interface RootCauseCardProps {
  diagnosis: {
    root_cause: string
    explanation: string
    fix: string
    kubectl_commands: string[]
    confidence: number
    confidence_reasoning: string
    prevention: string
  }
}

export function RootCauseCard({
  diagnosis,
}: RootCauseCardProps) {

  const confidence =
    diagnosis.confidence ?? 50

  return (

    <div className="
      soft-card
      bg-[#fffdf9]
      overflow-hidden
    ">

      {/* HEADER */}

      <div className="
        px-6
        sm:px-8
        py-6
        border-b
        border-[#eee4e7]
        bg-gradient-to-r
        from-[#fff7f9]
        to-[#f8f4fc]
      ">

        <div className="flex items-start justify-between gap-4">

          <div>

            <p className="
              text-xs
              uppercase
              tracking-[0.16em]
              text-[#a77c8c]
              font-bold
            ">
              AI investigation
            </p>

            <h2 className="
              font-serif
              text-3xl
              text-[#443d45]
              mt-1
            ">
              Diagnosis
            </h2>

          </div>

          <div className="
            w-11
            h-11
            rounded-full
            bg-[#f4dce5]
            flex
            items-center
            justify-center
          ">

            <AlertTriangle
              size={19}
              className="text-[#b6758c]"
            />

          </div>

        </div>

      </div>


      <div className="p-6 sm:p-8 space-y-7">


        {/* ROOT CAUSE */}

        <section>

          <div className="flex items-center gap-2 mb-2">

            <div className="
              w-6
              h-6
              rounded-full
              bg-[#f5dce5]
              flex
              items-center
              justify-center
            ">

              <span className="text-xs text-[#a86f84]">
                01
              </span>

            </div>

            <h3 className="
              text-xs
              uppercase
              tracking-[0.14em]
              font-bold
              text-[#81757e]
            ">
              Root cause
            </h3>

          </div>

          <p className="
            font-serif
            text-xl
            leading-relaxed
            text-[#443d45]
          ">
            {diagnosis.root_cause ||
              'Unable to determine root cause'}
          </p>

        </section>


        {/* EXPLANATION */}

        <section className="
          rounded-2xl
          bg-[#f7f3fb]
          p-5
        ">

          <h3 className="
            text-xs
            uppercase
            tracking-[0.14em]
            font-bold
            text-[#81758d]
            mb-2
          ">
            Explanation
          </h3>

          <p className="
            text-sm
            leading-7
            text-[#69606d]
          ">
            {diagnosis.explanation ||
              'No explanation provided'}
          </p>

        </section>


        {/* FIX */}

        <section>

          <h3 className="
            text-xs
            uppercase
            tracking-[0.14em]
            font-bold
            text-[#81757e]
            mb-2
          ">
            Suggested fix
          </h3>

          <div className="
            rounded-2xl
            bg-[#edf7f0]
            border
            border-[#d8eadc]
            p-5
          ">

            <p className="
              text-sm
              leading-7
              text-[#53675a]
              whitespace-pre-line
            ">
              {diagnosis.fix ||
                'No fix recommendation provided'}
            </p>

          </div>

        </section>


        {/* COMMANDS */}

        {diagnosis.kubectl_commands &&
          diagnosis.kubectl_commands.length > 0 && (

          <section>

            <div className="
              flex
              items-center
              gap-2
              mb-3
            ">

              <Terminal
                size={16}
                className="text-[#88759b]"
              />

              <h3 className="
                text-xs
                uppercase
                tracking-[0.14em]
                font-bold
                text-[#81757e]
              ">
                kubectl commands
              </h3>

            </div>


            <div className="space-y-2">

              {diagnosis.kubectl_commands.map(
                (command, index) => (

                <div
                  key={index}
                  className="
                    group
                    flex
                    items-center
                    gap-3
                    bg-[#29252a]
                    text-[#f8f1f4]
                    rounded-xl
                    px-4
                    py-3
                    overflow-x-auto
                  "
                >

                  <span className="
                    text-[#d7aabb]
                    text-xs
                  ">
                    $
                  </span>

                  <code className="
                    text-xs
                    font-mono
                    flex-1
                    whitespace-nowrap
                  ">
                    {command}
                  </code>

                </div>

              ))}

            </div>

          </section>

        )}


        {/* CONFIDENCE */}

        <section className="
          rounded-2xl
          bg-[#fff7e7]
          border
          border-[#f0dfb8]
          p-5
        ">

          <div className="
            flex
            items-center
            justify-between
            gap-4
          ">

            <div>

              <h3 className="
                text-xs
                uppercase
                tracking-[0.14em]
                font-bold
                text-[#88734d]
              ">
                Confidence
              </h3>

              <div className="
                text-3xl
                font-serif
                text-[#66563a]
                mt-1
              ">
                {confidence}%
              </div>

            </div>


            <div className="
              w-16
              h-16
              rounded-full
              border-[5px]
              border-[#ead9af]
              flex
              items-center
              justify-center
            ">

              <span className="text-xs font-bold text-[#79633b]">
                AI
              </span>

            </div>

          </div>


          {diagnosis.confidence_reasoning && (

            <p className="
              mt-3
              text-xs
              leading-6
              text-[#806f51]
            ">
              {diagnosis.confidence_reasoning}
            </p>

          )}

        </section>


        {/* PREVENTION */}

        {diagnosis.prevention && (

          <section>

            <div className="
              flex
              items-center
              gap-2
              mb-2
            ">

              <ShieldCheck
                size={17}
                className="text-[#71927c]"
              />

              <h3 className="
                text-xs
                uppercase
                tracking-[0.14em]
                font-bold
                text-[#81757e]
              ">
                Prevention
              </h3>

            </div>

            <p className="
              text-sm
              leading-7
              text-[#69606d]
            ">
              {diagnosis.prevention}
            </p>

          </section>

        )}

      </div>

    </div>
  )
}